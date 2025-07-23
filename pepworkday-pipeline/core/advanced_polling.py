"""
Advanced Polling System for PepWorkday Pipeline.

This module implements sophisticated scheduled polling of Samsara API endpoints
with intelligent pagination, rate limiting, exponential backoff, and data
persistence for the PepWorkday pipeline.

Features:
- Intelligent pagination handling
- Exponential backoff on rate limits
- Data deduplication and incremental updates
- Comprehensive error handling and recovery
- Metrics collection and monitoring
- Integration with Google Sheets and Slack

PepWorkday Configuration:
- Organization ID: 5005620
- Group ID: 129031
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json

from ..utils.samsara_api import (
    create_samsara_client,
    SamsaraAPIClient,
    SamsaraAPIError,
    trips_to_dataframe,
    vehicle_locations_to_dataframe,
    driver_stats_to_dataframe
)
from ..integrations.google_sheets import GoogleSheetsClient
from ..integrations.slack_notifications import SlackNotifier, create_pipeline_summary_metrics
from ..config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class PollingMetrics:
    """Container for polling operation metrics."""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limited_requests: int = 0
    total_records_fetched: int = 0
    unique_records: int = 0
    duplicate_records: int = 0
    api_response_times: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    @property
    def duration_seconds(self) -> float:
        """Calculate total polling duration."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    @property
    def success_rate(self) -> float:
        """Calculate request success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def average_response_time(self) -> float:
        """Calculate average API response time."""
        if not self.api_response_times:
            return 0.0
        return sum(self.api_response_times) / len(self.api_response_times)


@dataclass
class PollingConfig:
    """Configuration for advanced polling operations."""
    # Polling intervals
    default_interval_seconds: int = 300  # 5 minutes
    max_interval_seconds: int = 3600     # 1 hour
    min_interval_seconds: int = 60       # 1 minute
    
    # Rate limiting
    max_requests_per_minute: int = 60
    rate_limit_backoff_factor: float = 2.0
    max_backoff_seconds: int = 300
    
    # Pagination
    default_page_size: int = 1000
    max_pages_per_request: int = 100
    
    # Data management
    enable_deduplication: bool = True
    max_data_age_hours: int = 24
    incremental_updates: bool = True
    
    # Concurrency
    max_concurrent_requests: int = 5
    request_timeout_seconds: int = 30
    
    # Error handling
    max_retries: int = 3
    retry_delay_seconds: int = 5


class AdvancedSamsaraPoller:
    """Advanced polling system for Samsara API with intelligent features."""
    
    def __init__(self, config: Optional[PollingConfig] = None):
        """
        Initialize the advanced poller.
        
        Args:
            config: Polling configuration (uses defaults if not provided)
        """
        self.config = config or PollingConfig()
        self.api_client = create_samsara_client()
        self.metrics = PollingMetrics()
        
        # Data tracking
        self.seen_records: Set[str] = set()
        self.last_poll_times: Dict[str, datetime] = {}
        
        # Rate limiting
        self.request_times: List[datetime] = []
        self.current_backoff_delay = 0
        
        # Integration clients
        self.sheets_client: Optional[GoogleSheetsClient] = None
        self.slack_notifier: Optional[SlackNotifier] = None
        
        logger.info("Initialized Advanced Samsara Poller for PepWorkday")
    
    def initialize_integrations(self):
        """Initialize Google Sheets and Slack integrations."""
        try:
            self.sheets_client = GoogleSheetsClient(
                credentials_path=settings.google_sheets.credentials_path,
                spreadsheet_id=settings.google_sheets.spreadsheet_id
            )
            
            self.slack_notifier = SlackNotifier(
                bot_token=settings.slack.bot_token,
                webhook_url=settings.slack.webhook_url,
                default_channel=settings.slack.channel
            )
            
            logger.info("Initialized polling integrations")
            
        except Exception as e:
            logger.error(f"Error initializing integrations: {str(e)}")
    
    def poll_fleet_data(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        data_types: Optional[List[str]] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Poll comprehensive fleet data from Samsara API.
        
        Args:
            start_time: Start time for data retrieval
            end_time: End time for data retrieval
            data_types: List of data types to retrieve
            
        Returns:
            Dictionary of DataFrames keyed by data type
        """
        logger.info("Starting advanced fleet data polling")
        self.metrics = PollingMetrics()
        
        # Set default time range
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time - timedelta(hours=1)
        
        # Set default data types
        if not data_types:
            data_types = ['trips', 'locations', 'driver_stats', 'vehicle_stats']
        
        results = {}
        
        try:
            # Poll each data type
            for data_type in data_types:
                logger.info(f"Polling {data_type} data")
                
                try:
                    data = self._poll_data_type(data_type, start_time, end_time)
                    if not data.empty:
                        results[data_type] = data
                        logger.info(f"Retrieved {len(data)} {data_type} records")
                    else:
                        logger.info(f"No {data_type} data available")
                        
                except Exception as e:
                    logger.error(f"Error polling {data_type}: {str(e)}")
                    self.metrics.errors.append(f"{data_type}: {str(e)}")
            
            # Update metrics
            self.metrics.end_time = datetime.now()
            self.metrics.total_records_fetched = sum(len(df) for df in results.values())
            
            # Process and store results
            if results:
                self._process_polling_results(results)
            
            # Send success notification
            if self.slack_notifier and results:
                self._send_polling_notification(results, success=True)
            
            logger.info(f"Polling completed successfully. Retrieved {self.metrics.total_records_fetched} total records")
            return results
            
        except Exception as e:
            logger.error(f"Polling failed: {str(e)}")
            self.metrics.errors.append(str(e))
            
            # Send error notification
            if self.slack_notifier:
                self._send_polling_notification({}, success=False, error=str(e))
            
            raise
    
    def _poll_data_type(
        self,
        data_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> pd.DataFrame:
        """Poll a specific data type with pagination and rate limiting."""
        all_data = []
        page = 1
        
        while page <= self.config.max_pages_per_request:
            # Check rate limits
            self._enforce_rate_limits()
            
            try:
                # Make API request with timing
                request_start = time.time()
                
                if data_type == 'trips':
                    page_data = self.api_client.get_fleet_trips(
                        start_time, end_time, limit=self.config.default_page_size
                    )
                elif data_type == 'locations':
                    page_data = self.api_client.get_vehicle_locations()
                elif data_type == 'driver_stats':
                    page_data = self.api_client.get_driver_stats(start_time, end_time)
                elif data_type == 'vehicle_stats':
                    page_data = self.api_client.get_vehicle_stats(start_time, end_time)
                else:
                    logger.warning(f"Unknown data type: {data_type}")
                    break
                
                request_time = time.time() - request_start
                self.metrics.api_response_times.append(request_time)
                self.metrics.successful_requests += 1
                
                # Process page data
                if not page_data:
                    break
                
                # Deduplicate if enabled
                if self.config.enable_deduplication:
                    page_data = self._deduplicate_records(page_data, data_type)
                
                all_data.extend(page_data)
                
                # Check if we have more pages
                if len(page_data) < self.config.default_page_size:
                    break
                
                page += 1
                
            except SamsaraAPIError as e:
                self.metrics.failed_requests += 1
                
                if "rate limit" in str(e).lower() or "429" in str(e):
                    self.metrics.rate_limited_requests += 1
                    self._handle_rate_limit()
                    continue
                else:
                    logger.error(f"API error polling {data_type}: {str(e)}")
                    break
            
            except Exception as e:
                self.metrics.failed_requests += 1
                logger.error(f"Unexpected error polling {data_type}: {str(e)}")
                break
        
        # Convert to DataFrame
        if all_data:
            if data_type == 'trips':
                return trips_to_dataframe(all_data)
            elif data_type == 'locations':
                return vehicle_locations_to_dataframe(all_data)
            elif data_type in ['driver_stats', 'vehicle_stats']:
                return driver_stats_to_dataframe(all_data)
        
        return pd.DataFrame()
    
    def _enforce_rate_limits(self):
        """Enforce API rate limits with intelligent backoff."""
        now = datetime.now()
        
        # Clean old request times
        cutoff = now - timedelta(minutes=1)
        self.request_times = [t for t in self.request_times if t > cutoff]
        
        # Check if we're at the rate limit
        if len(self.request_times) >= self.config.max_requests_per_minute:
            sleep_time = 60 - (now - self.request_times[0]).total_seconds()
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f} seconds")
                time.sleep(sleep_time)
        
        # Apply current backoff delay
        if self.current_backoff_delay > 0:
            logger.info(f"Applying backoff delay: {self.current_backoff_delay} seconds")
            time.sleep(self.current_backoff_delay)
            self.current_backoff_delay = 0
        
        # Record this request time
        self.request_times.append(now)
        self.metrics.total_requests += 1
    
    def _handle_rate_limit(self):
        """Handle rate limit responses with exponential backoff."""
        if self.current_backoff_delay == 0:
            self.current_backoff_delay = self.config.retry_delay_seconds
        else:
            self.current_backoff_delay = min(
                self.current_backoff_delay * self.config.rate_limit_backoff_factor,
                self.config.max_backoff_seconds
            )
        
        logger.warning(f"Rate limited, will backoff for {self.current_backoff_delay} seconds")
    
    def _deduplicate_records(self, records: List[Dict], data_type: str) -> List[Dict]:
        """Deduplicate records based on unique identifiers."""
        unique_records = []
        
        for record in records:
            # Generate unique identifier based on data type
            if data_type == 'trips':
                record_id = record.get('id', '')
            elif data_type == 'locations':
                record_id = f"{record.get('vehicleId', '')}_{record.get('time', '')}"
            elif data_type in ['driver_stats', 'vehicle_stats']:
                record_id = f"{record.get('driverId', record.get('vehicleId', ''))}_{data_type}"
            else:
                record_id = str(hash(json.dumps(record, sort_keys=True)))
            
            # Create hash for deduplication
            record_hash = hashlib.md5(f"{data_type}_{record_id}".encode()).hexdigest()
            
            if record_hash not in self.seen_records:
                self.seen_records.add(record_hash)
                unique_records.append(record)
                self.metrics.unique_records += 1
            else:
                self.metrics.duplicate_records += 1
        
        return unique_records
    
    def _process_polling_results(self, results: Dict[str, pd.DataFrame]):
        """Process and store polling results."""
        try:
            if not self.sheets_client:
                logger.warning("Google Sheets client not initialized, skipping data storage")
                return
            
            # Store each data type in appropriate worksheet
            worksheet_mapping = {
                'trips': 'PolledTrips',
                'locations': 'PolledLocations',
                'driver_stats': 'PolledDriverStats',
                'vehicle_stats': 'PolledVehicleStats'
            }
            
            for data_type, df in results.items():
                worksheet_name = worksheet_mapping.get(data_type, f'Polled{data_type.title()}')
                
                # Add polling metadata
                df['polling_timestamp'] = datetime.now().isoformat()
                df['polling_batch_id'] = f"poll_{int(time.time())}"
                
                # Upsert to Google Sheets
                self.sheets_client.upsert_data(
                    worksheet_name=worksheet_name,
                    data=df,
                    key_column='polling_batch_id' if 'id' not in df.columns else 'id'
                )
                
                logger.info(f"Stored {len(df)} {data_type} records in {worksheet_name}")
            
        except Exception as e:
            logger.error(f"Error processing polling results: {str(e)}")
    
    def _send_polling_notification(
        self,
        results: Dict[str, pd.DataFrame],
        success: bool,
        error: Optional[str] = None
    ):
        """Send Slack notification about polling results."""
        try:
            if success:
                total_records = sum(len(df) for df in results.values())
                
                metrics = create_pipeline_summary_metrics(
                    total_records=total_records,
                    processed_records=total_records,
                    inserted_records=total_records,
                    updated_records=0,
                    processing_time=self.metrics.duration_seconds
                )
                
                message = f"🔄 PepWorkday Polling Completed: {total_records} records retrieved"
                self.slack_notifier.send_success_notification(message, metrics)
                
            else:
                message = f"❌ PepWorkday Polling Failed"
                errors = [error] if error else self.metrics.errors
                self.slack_notifier.send_error_notification(message, errors)
                
        except Exception as e:
            logger.error(f"Error sending polling notification: {str(e)}")
    
    def run_continuous_polling(
        self,
        interval_seconds: Optional[int] = None,
        data_types: Optional[List[str]] = None
    ):
        """Run continuous polling with the specified interval."""
        interval = interval_seconds or self.config.default_interval_seconds
        
        logger.info(f"Starting continuous polling every {interval} seconds")
        
        while True:
            try:
                # Calculate time range for this poll
                end_time = datetime.now()
                start_time = end_time - timedelta(seconds=interval * 2)  # Overlap for safety
                
                # Poll data
                results = self.poll_fleet_data(
                    start_time=start_time,
                    end_time=end_time,
                    data_types=data_types
                )
                
                logger.info(f"Polling cycle completed, sleeping for {interval} seconds")
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Continuous polling stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in continuous polling: {str(e)}")
                time.sleep(interval)  # Continue polling despite errors


def create_advanced_poller(config: Optional[PollingConfig] = None) -> AdvancedSamsaraPoller:
    """Create and configure an advanced poller for PepWorkday."""
    poller = AdvancedSamsaraPoller(config)
    poller.initialize_integrations()
    return poller


if __name__ == "__main__":
    # Example usage
    poller = create_advanced_poller()
    
    # Run a single polling cycle
    results = poller.poll_fleet_data()
    print(f"Retrieved {sum(len(df) for df in results.values())} total records")
    
    # Or run continuous polling
    # poller.run_continuous_polling(interval_seconds=300)
