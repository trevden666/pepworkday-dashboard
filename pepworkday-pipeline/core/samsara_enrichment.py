"""
Samsara data enrichment module for the PepWorkday pipeline.

Chain of thought:
1. Load Samsara trip data from CSV/Excel files or API
2. Merge with dispatch data based on driver/date matching
3. Calculate key metrics: actual vs planned miles, stops per driver, idle percentage
4. Handle data quality issues like missing matches or inconsistent formats
5. Provide detailed reporting on enrichment success rates and data quality
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
import logging
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass
import requests
import json
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


@dataclass
class EnrichmentMetrics:
    """Container for enrichment operation metrics."""
    total_dispatch_records: int
    total_samsara_records: int
    matched_records: int
    unmatched_dispatch: int
    unmatched_samsara: int
    match_rate: float
    avg_miles_variance: float
    avg_stops_variance: float
    avg_idle_percentage: float


class SamsaraEnrichmentError(Exception):
    """Custom exception for Samsara enrichment operations."""
    pass


class SamsaraAPIClient:
    """Client for Samsara API integration."""

    def __init__(self, api_token: str, base_url: str = "https://api.samsara.com"):
        """
        Initialize Samsara API client.

        Args:
            api_token: Samsara API token
            base_url: Base URL for Samsara API
        """
        self.api_token = api_token
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        logger.info("Initialized Samsara API client")

    def get_trips_data(
        self,
        start_date: datetime,
        end_date: datetime,
        driver_ids: Optional[List[str]] = None,
        vehicle_ids: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Fetch trips data from Samsara API.

        Args:
            start_date: Start date for trip data
            end_date: End date for trip data
            driver_ids: Optional list of driver IDs to filter
            vehicle_ids: Optional list of vehicle IDs to filter

        Returns:
            pandas.DataFrame: Trip data from Samsara API
        """
        logger.info(f"Fetching Samsara trips data from {start_date} to {end_date}")

        try:
            # Prepare API request parameters
            params = {
                'startTime': start_date.isoformat(),
                'endTime': end_date.isoformat(),
                'limit': 1000  # Adjust based on API limits
            }

            if driver_ids:
                params['driverIds'] = driver_ids
            if vehicle_ids:
                params['vehicleIds'] = vehicle_ids

            # Make API request
            url = urljoin(self.base_url, '/fleet/trips')
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            # Parse response
            data = response.json()
            trips = data.get('data', [])

            if not trips:
                logger.warning("No trips data returned from Samsara API")
                return pd.DataFrame()

            # Convert to DataFrame
            df = pd.DataFrame(trips)
            df = self._process_api_trips_data(df)

            logger.info(f"Successfully fetched {len(df)} trips from Samsara API")
            return df

        except requests.RequestException as e:
            error_msg = f"Failed to fetch data from Samsara API: {str(e)}"
            logger.error(error_msg)
            raise SamsaraEnrichmentError(error_msg) from e
        except Exception as e:
            error_msg = f"Error processing Samsara API response: {str(e)}"
            logger.error(error_msg)
            raise SamsaraEnrichmentError(error_msg) from e

    def get_driver_stats(
        self,
        start_date: datetime,
        end_date: datetime,
        driver_ids: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Fetch driver statistics from Samsara API.

        Args:
            start_date: Start date for stats
            end_date: End date for stats
            driver_ids: Optional list of driver IDs to filter

        Returns:
            pandas.DataFrame: Driver statistics data
        """
        logger.info(f"Fetching Samsara driver stats from {start_date} to {end_date}")

        try:
            params = {
                'startTime': start_date.isoformat(),
                'endTime': end_date.isoformat()
            }

            if driver_ids:
                params['driverIds'] = driver_ids

            url = urljoin(self.base_url, '/fleet/drivers/stats')
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            stats = data.get('data', [])

            if not stats:
                logger.warning("No driver stats returned from Samsara API")
                return pd.DataFrame()

            df = pd.DataFrame(stats)
            df = self._process_api_driver_stats(df)

            logger.info(f"Successfully fetched stats for {len(df)} drivers from Samsara API")
            return df

        except requests.RequestException as e:
            error_msg = f"Failed to fetch driver stats from Samsara API: {str(e)}"
            logger.error(error_msg)
            raise SamsaraEnrichmentError(error_msg) from e
        except Exception as e:
            error_msg = f"Error processing Samsara API driver stats: {str(e)}"
            logger.error(error_msg)
            raise SamsaraEnrichmentError(error_msg) from e

    def _process_api_trips_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process trips data from Samsara API into standard format."""
        processed_df = df.copy()

        # Standardize column names to match file-based format
        column_mapping = {
            'id': 'trip_id',
            'driverId': 'driver_id',
            'vehicleId': 'vehicle_id',
            'startTime': 'trip_date',
            'endTime': 'trip_end_date',
            'distanceMiles': 'total_miles',
            'idleTimeMs': 'idle_time_ms',
            'fuelUsedMl': 'fuel_used_ml'
        }

        # Rename columns if they exist
        for old_name, new_name in column_mapping.items():
            if old_name in processed_df.columns:
                processed_df = processed_df.rename(columns={old_name: new_name})

        # Convert timestamps to datetime
        if 'trip_date' in processed_df.columns:
            processed_df['trip_date'] = pd.to_datetime(processed_df['trip_date'])

        # Convert idle time from milliseconds to minutes
        if 'idle_time_ms' in processed_df.columns:
            processed_df['idle_time'] = processed_df['idle_time_ms'] / (1000 * 60)  # ms to minutes

        # Convert fuel from ml to gallons (if needed)
        if 'fuel_used_ml' in processed_df.columns:
            processed_df['fuel_used'] = processed_df['fuel_used_ml'] / 3785.41  # ml to gallons

        # Add stops count if available in route data
        if 'route' in processed_df.columns:
            processed_df['stops_count'] = processed_df['route'].apply(
                lambda x: len(x.get('stops', [])) if isinstance(x, dict) else 0
            )

        return processed_df

    def _process_api_driver_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process driver statistics from Samsara API."""
        processed_df = df.copy()

        # Standardize column names
        column_mapping = {
            'driverId': 'driver_id',
            'driverName': 'driver_name',
            'totalDistanceMiles': 'total_miles',
            'totalIdleTimeMs': 'idle_time_ms',
            'totalDrivingTimeMs': 'driving_time_ms'
        }

        for old_name, new_name in column_mapping.items():
            if old_name in processed_df.columns:
                processed_df = processed_df.rename(columns={old_name: new_name})

        # Convert time fields from milliseconds to minutes
        time_fields = ['idle_time_ms', 'driving_time_ms']
        for field in time_fields:
            if field in processed_df.columns:
                new_field = field.replace('_ms', '')
                processed_df[new_field] = processed_df[field] / (1000 * 60)

        return processed_df


def load_samsara_data(
    file_path: Optional[Union[str, Path]] = None,
    api_client: Optional[SamsaraAPIClient] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    date_column: str = 'trip_date',
    driver_column: str = 'driver_id',
    driver_ids: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Load Samsara trip data from file or API.

    Args:
        file_path: Path to Samsara data file (for file-based loading)
        api_client: SamsaraAPIClient instance (for API-based loading)
        start_date: Start date for API data fetch
        end_date: End date for API data fetch
        date_column: Name of the date column
        driver_column: Name of the driver identifier column
        driver_ids: Optional list of driver IDs to filter (API only)

    Returns:
        pandas.DataFrame: Loaded and preprocessed Samsara data
    """
    if file_path and api_client:
        raise SamsaraEnrichmentError("Provide either file_path or api_client, not both")

    if not file_path and not api_client:
        raise SamsaraEnrichmentError("Must provide either file_path or api_client")

    # Load from file
    if file_path:
        return _load_samsara_from_file(file_path, date_column, driver_column)

    # Load from API
    if api_client:
        if not start_date or not end_date:
            raise SamsaraEnrichmentError("start_date and end_date required for API loading")

        return _load_samsara_from_api(api_client, start_date, end_date, driver_ids, date_column, driver_column)


def _load_samsara_from_file(
    file_path: Union[str, Path],
    date_column: str,
    driver_column: str
) -> pd.DataFrame:
    """Load Samsara data from file."""
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Samsara data file not found: {file_path}")

    logger.info(f"Loading Samsara data from file: {file_path}")

    try:
        # Load based on file extension
        if file_path.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path, engine='openpyxl')
        elif file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path)
        else:
            raise SamsaraEnrichmentError(f"Unsupported file format: {file_path.suffix}")

        # Preprocess the data
        df = _preprocess_samsara_data(df, date_column, driver_column)

        logger.info(f"Successfully loaded {len(df)} Samsara records from file")
        return df

    except Exception as e:
        error_msg = f"Failed to load Samsara data from {file_path}: {str(e)}"
        logger.error(error_msg)
        raise SamsaraEnrichmentError(error_msg) from e


def _load_samsara_from_api(
    api_client: SamsaraAPIClient,
    start_date: datetime,
    end_date: datetime,
    driver_ids: Optional[List[str]],
    date_column: str,
    driver_column: str
) -> pd.DataFrame:
    """Load Samsara data from API."""
    logger.info(f"Loading Samsara data from API for date range: {start_date} to {end_date}")

    try:
        # Fetch trips data from API
        df = api_client.get_trips_data(start_date, end_date, driver_ids)

        if df.empty:
            logger.warning("No Samsara data returned from API")
            return df

        # Preprocess the data (API data is already in standard format)
        df = _preprocess_samsara_data(df, date_column, driver_column)

        logger.info(f"Successfully loaded {len(df)} Samsara records from API")
        return df

    except Exception as e:
        error_msg = f"Failed to load Samsara data from API: {str(e)}"
        logger.error(error_msg)
        raise SamsaraEnrichmentError(error_msg) from e


def enrich_dispatch_data(
    dispatch_df: pd.DataFrame,
    samsara_df: pd.DataFrame,
    match_columns: Dict[str, str] = None,
    date_tolerance_days: int = 1
) -> Tuple[pd.DataFrame, EnrichmentMetrics]:
    """
    Enrich dispatch data with Samsara trip metrics.
    
    Args:
        dispatch_df: DataFrame containing dispatch data
        samsara_df: DataFrame containing Samsara trip data
        match_columns: Dict mapping dispatch columns to Samsara columns for matching
        date_tolerance_days: Number of days tolerance for date matching
        
    Returns:
        Tuple of (enriched_dataframe, enrichment_metrics)
    """
    logger.info("Starting dispatch data enrichment with Samsara data")
    
    # Set default matching columns if not provided
    if match_columns is None:
        match_columns = {
            'driver_name': 'driver_id',
            'date': 'trip_date'
        }
    
    # Validate required columns
    _validate_enrichment_columns(dispatch_df, samsara_df, match_columns)
    
    # Prepare data for matching
    dispatch_prepared = _prepare_dispatch_for_matching(dispatch_df, match_columns)
    samsara_prepared = _prepare_samsara_for_matching(samsara_df, match_columns)
    
    # Perform the enrichment merge
    enriched_df = _perform_enrichment_merge(
        dispatch_prepared, samsara_prepared, match_columns, date_tolerance_days
    )
    
    # Calculate derived metrics
    enriched_df = _calculate_derived_metrics(enriched_df)
    
    # Generate enrichment metrics
    metrics = _calculate_enrichment_metrics(dispatch_df, samsara_df, enriched_df)
    
    logger.info(f"Enrichment completed. Match rate: {metrics.match_rate:.2%}")
    return enriched_df, metrics


def _preprocess_samsara_data(
    df: pd.DataFrame, date_column: str, driver_column: str
) -> pd.DataFrame:
    """Preprocess Samsara data for consistent formatting."""
    processed_df = df.copy()
    
    # Normalize column names
    processed_df.columns = [col.lower().replace(' ', '_') for col in processed_df.columns]
    
    # Ensure date column is datetime
    if date_column in processed_df.columns:
        processed_df[date_column] = pd.to_datetime(processed_df[date_column], errors='coerce')
    
    # Clean driver identifiers
    if driver_column in processed_df.columns:
        processed_df[driver_column] = processed_df[driver_column].astype(str).str.strip()
    
    # Ensure numeric columns are properly typed
    numeric_columns = ['total_miles', 'idle_time', 'stops_count', 'fuel_used']
    for col in numeric_columns:
        if col in processed_df.columns:
            processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')
    
    # Remove rows with missing critical data
    critical_columns = [date_column, driver_column]
    processed_df = processed_df.dropna(subset=critical_columns)
    
    return processed_df


def _validate_enrichment_columns(
    dispatch_df: pd.DataFrame,
    samsara_df: pd.DataFrame,
    match_columns: Dict[str, str]
) -> None:
    """Validate that required columns exist for enrichment."""
    # Check dispatch columns
    missing_dispatch = [col for col in match_columns.keys() if col not in dispatch_df.columns]
    if missing_dispatch:
        raise SamsaraEnrichmentError(f"Missing dispatch columns: {missing_dispatch}")
    
    # Check Samsara columns
    missing_samsara = [col for col in match_columns.values() if col not in samsara_df.columns]
    if missing_samsara:
        raise SamsaraEnrichmentError(f"Missing Samsara columns: {missing_samsara}")


def _prepare_dispatch_for_matching(
    df: pd.DataFrame, match_columns: Dict[str, str]
) -> pd.DataFrame:
    """Prepare dispatch data for matching with Samsara data."""
    prepared_df = df.copy()
    
    # Normalize driver names for matching
    if 'driver_name' in match_columns:
        driver_col = match_columns['driver_name']
        if driver_col in prepared_df.columns:
            prepared_df['_normalized_driver'] = (
                prepared_df[driver_col].astype(str).str.lower().str.strip()
            )
    
    # Ensure date column is datetime
    if 'date' in match_columns:
        date_col = match_columns['date']
        if date_col in prepared_df.columns:
            prepared_df['_normalized_date'] = pd.to_datetime(
                prepared_df[date_col], errors='coerce'
            )
    
    return prepared_df


def _prepare_samsara_for_matching(
    df: pd.DataFrame, match_columns: Dict[str, str]
) -> pd.DataFrame:
    """Prepare Samsara data for matching with dispatch data."""
    prepared_df = df.copy()
    
    # Normalize driver identifiers for matching
    samsara_driver_col = match_columns.get('driver_name')
    if samsara_driver_col and samsara_driver_col in prepared_df.columns:
        prepared_df['_normalized_driver'] = (
            prepared_df[samsara_driver_col].astype(str).str.lower().str.strip()
        )
    
    # Ensure date column is datetime
    samsara_date_col = match_columns.get('date')
    if samsara_date_col and samsara_date_col in prepared_df.columns:
        prepared_df['_normalized_date'] = pd.to_datetime(
            prepared_df[samsara_date_col], errors='coerce'
        )
    
    return prepared_df


def _perform_enrichment_merge(
    dispatch_df: pd.DataFrame,
    samsara_df: pd.DataFrame,
    match_columns: Dict[str, str],
    date_tolerance_days: int
) -> pd.DataFrame:
    """Perform the actual merge between dispatch and Samsara data."""
    enriched_records = []
    
    for idx, dispatch_row in dispatch_df.iterrows():
        # Find matching Samsara records
        matches = _find_samsara_matches(
            dispatch_row, samsara_df, match_columns, date_tolerance_days
        )
        
        # Create enriched record
        enriched_record = dispatch_row.to_dict()
        
        if matches:
            # Use the best match (first one if multiple)
            best_match = matches.iloc[0]
            
            # Add Samsara metrics
            enriched_record.update({
                'samsara_total_miles': best_match.get('total_miles', np.nan),
                'samsara_idle_time': best_match.get('idle_time', np.nan),
                'samsara_stops_count': best_match.get('stops_count', np.nan),
                'samsara_fuel_used': best_match.get('fuel_used', np.nan),
                'samsara_match_found': True,
                'samsara_match_date': best_match.get('_normalized_date'),
                'samsara_match_driver': best_match.get('_normalized_driver')
            })
        else:
            # No match found
            enriched_record.update({
                'samsara_total_miles': np.nan,
                'samsara_idle_time': np.nan,
                'samsara_stops_count': np.nan,
                'samsara_fuel_used': np.nan,
                'samsara_match_found': False,
                'samsara_match_date': None,
                'samsara_match_driver': None
            })
        
        enriched_records.append(enriched_record)
    
    return pd.DataFrame(enriched_records)


def _find_samsara_matches(
    dispatch_row: pd.Series,
    samsara_df: pd.DataFrame,
    match_columns: Dict[str, str],
    date_tolerance_days: int
) -> pd.DataFrame:
    """Find matching Samsara records for a dispatch row."""
    matches = samsara_df.copy()
    
    # Filter by driver if available
    if '_normalized_driver' in dispatch_row and '_normalized_driver' in matches.columns:
        dispatch_driver = dispatch_row['_normalized_driver']
        if pd.notna(dispatch_driver):
            matches = matches[matches['_normalized_driver'] == dispatch_driver]
    
    # Filter by date with tolerance if available
    if '_normalized_date' in dispatch_row and '_normalized_date' in matches.columns:
        dispatch_date = dispatch_row['_normalized_date']
        if pd.notna(dispatch_date):
            date_min = dispatch_date - timedelta(days=date_tolerance_days)
            date_max = dispatch_date + timedelta(days=date_tolerance_days)
            matches = matches[
                (matches['_normalized_date'] >= date_min) &
                (matches['_normalized_date'] <= date_max)
            ]
    
    return matches


def _calculate_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate derived metrics from the enriched data."""
    enriched_df = df.copy()
    
    # Miles variance (actual vs planned)
    if 'planned_miles' in df.columns and 'samsara_total_miles' in df.columns:
        enriched_df['miles_variance'] = (
            enriched_df['samsara_total_miles'] - enriched_df['planned_miles']
        )
        enriched_df['miles_variance_percent'] = (
            enriched_df['miles_variance'] / enriched_df['planned_miles'] * 100
        ).round(2)
    
    # Stops variance (actual vs planned)
    if 'planned_stops' in df.columns and 'samsara_stops_count' in df.columns:
        enriched_df['stops_variance'] = (
            enriched_df['samsara_stops_count'] - enriched_df['planned_stops']
        )
        enriched_df['stops_variance_percent'] = (
            enriched_df['stops_variance'] / enriched_df['planned_stops'] * 100
        ).round(2)
    
    # Idle percentage (idle time / total trip time)
    if 'samsara_idle_time' in df.columns and 'samsara_total_miles' in df.columns:
        # Estimate total trip time based on miles (assuming average speed)
        avg_speed_mph = 35  # Configurable assumption
        enriched_df['estimated_trip_hours'] = enriched_df['samsara_total_miles'] / avg_speed_mph
        enriched_df['idle_percentage'] = (
            enriched_df['samsara_idle_time'] / 
            (enriched_df['estimated_trip_hours'] * 60) * 100  # Convert hours to minutes
        ).round(2)
    
    return enriched_df


def _calculate_enrichment_metrics(
    dispatch_df: pd.DataFrame,
    samsara_df: pd.DataFrame,
    enriched_df: pd.DataFrame
) -> EnrichmentMetrics:
    """Calculate metrics about the enrichment operation."""
    total_dispatch = len(dispatch_df)
    total_samsara = len(samsara_df)
    matched = len(enriched_df[enriched_df['samsara_match_found'] == True])
    unmatched_dispatch = total_dispatch - matched
    unmatched_samsara = total_samsara - matched  # Approximation
    
    match_rate = matched / total_dispatch if total_dispatch > 0 else 0
    
    # Calculate average variances for matched records
    matched_records = enriched_df[enriched_df['samsara_match_found'] == True]
    
    avg_miles_variance = 0
    if 'miles_variance' in matched_records.columns:
        avg_miles_variance = matched_records['miles_variance'].mean()
        if pd.isna(avg_miles_variance):
            avg_miles_variance = 0
    
    avg_stops_variance = 0
    if 'stops_variance' in matched_records.columns:
        avg_stops_variance = matched_records['stops_variance'].mean()
        if pd.isna(avg_stops_variance):
            avg_stops_variance = 0
    
    avg_idle_percentage = 0
    if 'idle_percentage' in matched_records.columns:
        avg_idle_percentage = matched_records['idle_percentage'].mean()
        if pd.isna(avg_idle_percentage):
            avg_idle_percentage = 0
    
    return EnrichmentMetrics(
        total_dispatch_records=total_dispatch,
        total_samsara_records=total_samsara,
        matched_records=matched,
        unmatched_dispatch=unmatched_dispatch,
        unmatched_samsara=unmatched_samsara,
        match_rate=match_rate,
        avg_miles_variance=avg_miles_variance,
        avg_stops_variance=avg_stops_variance,
        avg_idle_percentage=avg_idle_percentage
    )
