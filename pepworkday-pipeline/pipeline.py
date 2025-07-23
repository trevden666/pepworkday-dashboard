"""
Main CLI interface for the PepWorkday pipeline.

Chain of thought:
1. Provide a comprehensive CLI with click for easy command-line usage
2. Orchestrate the full pipeline: ingest → validate → normalize → enrich → upload → notify
3. Support both file-based and API-based Samsara data sources
4. Include dry-run mode for testing without making changes
5. Provide detailed logging and error reporting throughout the process
"""

import click
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import pandas as pd

from .core.excel_ingestion import load_excel, validate_schema, normalize_columns, DISPATCH_SCHEMA
from .core.samsara_enrichment import load_samsara_data, enrich_dispatch_data, SamsaraAPIClient
from .integrations.google_sheets import GoogleSheetsClient
from .integrations.slack_notifications import SlackNotifier, create_pipeline_summary_metrics
from .utils.samsara_api import (
    create_samsara_client,
    trips_to_dataframe,
    vehicle_locations_to_dataframe,
    addresses_to_dataframe
)
from .config.settings import settings
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class PipelineError(Exception):
    """Custom exception for pipeline errors."""
    pass


@click.command()
@click.option(
    '--excel',
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help='Path to Excel dispatch file to process'
)
@click.option(
    '--samsara-file',
    type=click.Path(exists=True, path_type=Path),
    help='Path to Samsara data file (CSV/Excel). If not provided, will use Samsara API'
)
@click.option(
    '--dry-run',
    is_flag=True,
    default=False,
    help='Run pipeline without making changes to Google Sheets or sending notifications'
)
@click.option(
    '--start-date',
    type=click.DateTime(formats=['%Y-%m-%d']),
    help='Start date for Samsara API data (YYYY-MM-DD). Defaults to yesterday'
)
@click.option(
    '--end-date',
    type=click.DateTime(formats=['%Y-%m-%d']),
    help='End date for Samsara API data (YYYY-MM-DD). Defaults to today'
)
@click.option(
    '--log-level',
    type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
    default='INFO',
    help='Set logging level'
)
@click.option(
    '--worksheet-name',
    default='RawData',
    help='Google Sheets worksheet name to update'
)
@click.option(
    '--slack-channel',
    help='Slack channel for notifications (overrides default)'
)
@click.option(
    '--include-locations',
    is_flag=True,
    default=False,
    help='Include current vehicle locations in the processing (PEPMove specific)'
)
@click.option(
    '--pepmove-summary',
    is_flag=True,
    default=False,
    help='Generate comprehensive PEPMove fleet summary'
)
def main(
    excel: Path,
    samsara_file: Optional[Path],
    dry_run: bool,
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    log_level: str,
    worksheet_name: str,
    slack_channel: Optional[str],
    include_locations: bool,
    pepmove_summary: bool
):
    """
    PepWorkday Pipeline - Automate dispatch and Samsara data processing for PEPMove.

    This pipeline ingests Excel dispatch reports, enriches them with Samsara trip data,
    validates and normalizes the data, then syncs to Google Sheets with Slack notifications.

    PEPMove Configuration:
    - Organization ID: 5005620
    - Group ID: 129031
    - API Token: samsara_api_7qCpNNFjxM5S4jojGWzO9vxciB8o8I
    """
    # Configure logging
    logging.basicConfig(level=getattr(logging, log_level))
    
    # Set default date range if not provided
    if not start_date:
        start_date = datetime.now() - timedelta(days=1)
    if not end_date:
        end_date = datetime.now()
    
    logger.info(
        "Starting PepWorkday pipeline",
        excel_file=str(excel),
        samsara_file=str(samsara_file) if samsara_file else "API",
        dry_run=dry_run,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )
    
    pipeline_start_time = datetime.now()
    
    try:
        # Initialize pipeline components
        slack_notifier = _initialize_slack_notifier(slack_channel)
        
        # Step 1: Load and validate Excel dispatch data
        logger.info("Step 1: Loading Excel dispatch data")
        dispatch_df = load_excel(excel)
        
        validation_results = validate_schema(dispatch_df, DISPATCH_SCHEMA)
        if not validation_results['is_valid'] and settings.pipeline.strict_schema_validation:
            raise PipelineError(f"Excel validation failed: {validation_results['errors']}")
        
        # Step 2: Normalize dispatch data
        logger.info("Step 2: Normalizing dispatch data")
        dispatch_df = normalize_columns(dispatch_df)
        
        # Step 3: Load Samsara data (file or API)
        logger.info("Step 3: Loading Samsara data")
        samsara_df = _load_samsara_data(samsara_file, start_date, end_date)
        
        # Step 4: Enrich dispatch data with Samsara metrics
        logger.info("Step 4: Enriching dispatch data with Samsara metrics")
        enriched_df, enrichment_metrics = enrich_dispatch_data(dispatch_df, samsara_df)

        # Step 4.5: Add PEPMove-specific data if requested
        if include_locations or pepmove_summary:
            logger.info("Step 4.5: Adding PEPMove-specific data")
            enriched_df = _add_pepmove_specific_data(enriched_df, include_locations, pepmove_summary)
        
        # Step 5: Upload to Google Sheets (unless dry run)
        upload_results = None
        if not dry_run:
            logger.info("Step 5: Uploading to Google Sheets")
            upload_results = _upload_to_google_sheets(enriched_df, worksheet_name)
        else:
            logger.info("Step 5: Skipping Google Sheets upload (dry run mode)")
            upload_results = {'inserted': 0, 'updated': 0, 'errors': []}
        
        # Step 6: Send success notification (unless dry run)
        if not dry_run and settings.pipeline.enable_slack_notifications:
            logger.info("Step 6: Sending success notification")
            _send_success_notification(
                slack_notifier,
                enriched_df,
                enrichment_metrics,
                upload_results,
                pipeline_start_time,
                slack_channel
            )
        else:
            logger.info("Step 6: Skipping notifications (dry run mode or disabled)")
        
        # Pipeline completed successfully
        pipeline_duration = (datetime.now() - pipeline_start_time).total_seconds()
        logger.info(
            "Pipeline completed successfully",
            duration_seconds=pipeline_duration,
            records_processed=len(enriched_df),
            match_rate=enrichment_metrics.match_rate
        )
        
        if dry_run:
            click.echo("\n🔍 DRY RUN SUMMARY:")
            click.echo(f"✅ Would process {len(enriched_df)} records")
            click.echo(f"📊 Samsara match rate: {enrichment_metrics.match_rate:.1%}")
            click.echo(f"⏱️  Processing time: {pipeline_duration:.1f}s")
            click.echo("🚫 No changes made (dry run mode)")
        
    except Exception as e:
        pipeline_duration = (datetime.now() - pipeline_start_time).total_seconds()
        logger.error(
            "Pipeline failed",
            error=str(e),
            duration_seconds=pipeline_duration,
            exc_info=True
        )
        
        # Send error notification
        if not dry_run and settings.pipeline.enable_slack_notifications:
            _send_error_notification(slack_notifier, str(e), slack_channel)
        
        click.echo(f"❌ Pipeline failed: {str(e)}", err=True)
        sys.exit(1)


def _initialize_slack_notifier(channel: Optional[str]) -> Optional[SlackNotifier]:
    """Initialize Slack notifier if configured."""
    try:
        return SlackNotifier(
            bot_token=settings.slack.bot_token,
            webhook_url=settings.slack.webhook_url,
            default_channel=channel or settings.slack.channel
        )
    except Exception as e:
        logger.warning(f"Failed to initialize Slack notifier: {str(e)}")
        return None


def _load_samsara_data(
    samsara_file: Optional[Path],
    start_date: datetime,
    end_date: datetime
) -> pd.DataFrame:
    """Load Samsara data from file or API."""
    if samsara_file:
        # Load from file
        logger.info(f"Loading Samsara data from file: {samsara_file}")
        return load_samsara_data(file_path=samsara_file)
    else:
        # Load from API
        logger.info(f"Loading Samsara data from API for {start_date} to {end_date}")
        if not settings.samsara.use_api:
            raise PipelineError("Samsara API is disabled in settings but no file provided")
        
        api_client = create_samsara_client()
        trips_data = api_client.get_fleet_trips(start_date, end_date)
        samsara_df = trips_to_dataframe(trips_data)
        
        if samsara_df.empty:
            logger.warning("No Samsara data returned from API")
        
        return samsara_df


def _upload_to_google_sheets(df: pd.DataFrame, worksheet_name: str) -> Dict[str, Any]:
    """Upload enriched data to Google Sheets."""
    try:
        sheets_client = GoogleSheetsClient(
            credentials_path=settings.google_sheets.credentials_path,
            spreadsheet_id=settings.google_sheets.spreadsheet_id
        )
        
        return sheets_client.upsert_data(
            worksheet_name=worksheet_name,
            data=df,
            key_column='_kp_job_id',
            batch_size=settings.pipeline.batch_size
        )
        
    except Exception as e:
        logger.error(f"Failed to upload to Google Sheets: {str(e)}")
        raise PipelineError(f"Google Sheets upload failed: {str(e)}") from e


def _send_success_notification(
    slack_notifier: Optional[SlackNotifier],
    enriched_df: pd.DataFrame,
    enrichment_metrics,
    upload_results: Dict[str, Any],
    start_time: datetime,
    channel: Optional[str]
) -> None:
    """Send success notification to Slack."""
    if not slack_notifier:
        return
    
    processing_time = (datetime.now() - start_time).total_seconds()
    
    metrics = create_pipeline_summary_metrics(
        total_records=len(enriched_df),
        processed_records=len(enriched_df),
        inserted_records=upload_results.get('inserted', 0),
        updated_records=upload_results.get('updated', 0),
        processing_time=processing_time,
        match_rate=enrichment_metrics.match_rate,
        avg_miles_variance=enrichment_metrics.avg_miles_variance,
        avg_stops_variance=enrichment_metrics.avg_stops_variance,
        avg_idle_percentage=enrichment_metrics.avg_idle_percentage
    )
    
    message = f"PepWorkday pipeline completed successfully! Processed {len(enriched_df)} records with {enrichment_metrics.match_rate:.1%} Samsara match rate."
    
    slack_notifier.send_success_notification(message, metrics, channel)


def _add_pepmove_specific_data(
    df: pd.DataFrame,
    include_locations: bool,
    pepmove_summary: bool
) -> pd.DataFrame:
    """Add PEPMove-specific data to the enriched DataFrame."""
    enhanced_df = df.copy()

    try:
        api_client = create_samsara_client()

        # Add current vehicle locations if requested
        if include_locations:
            logger.info("Adding current vehicle locations for PEPMove fleet")
            locations = api_client.get_vehicle_locations()
            locations_df = vehicle_locations_to_dataframe(locations)

            if not locations_df.empty:
                # Add location data to main DataFrame if vehicle IDs match
                if 'vehicle_id' in enhanced_df.columns:
                    location_summary = locations_df.groupby('vehicle_id').agg({
                        'latitude': 'last',
                        'longitude': 'last',
                        'speed_mph': 'last',
                        'timestamp': 'last'
                    }).reset_index()

                    enhanced_df = enhanced_df.merge(
                        location_summary,
                        on='vehicle_id',
                        how='left',
                        suffixes=('', '_current')
                    )

                    logger.info(f"Added location data for {len(location_summary)} vehicles")

        # Add PEPMove fleet summary data if requested
        if pepmove_summary:
            logger.info("Generating PEPMove fleet summary")
            fleet_summary = api_client.get_pepmove_fleet_summary()

            # Add summary metadata to DataFrame
            enhanced_df['pepmove_org_id'] = fleet_summary['organization_id']
            enhanced_df['pepmove_group_id'] = fleet_summary['group_id']
            enhanced_df['fleet_total_vehicles'] = fleet_summary['total_vehicles']
            enhanced_df['summary_timestamp'] = fleet_summary['timestamp']

            logger.info(f"Added PEPMove fleet summary (Org: {fleet_summary['organization_id']}, "
                       f"Group: {fleet_summary['group_id']}, Vehicles: {fleet_summary['total_vehicles']})")

        return enhanced_df

    except Exception as e:
        logger.warning(f"Failed to add PEPMove-specific data: {str(e)}")
        return enhanced_df


def _send_error_notification(
    slack_notifier: Optional[SlackNotifier],
    error_message: str,
    channel: Optional[str]
) -> None:
    """Send error notification to Slack."""
    if not slack_notifier:
        return

    message = "PepWorkday pipeline failed with errors."
    errors = [error_message]

    slack_notifier.send_error_notification(message, errors, channel=channel)


if __name__ == '__main__':
    main()
