"""
Samsara API utility module for the PepWorkday pipeline.

This module provides a centralized interface for all Samsara API operations,
including authentication, rate limiting, error handling, and data formatting.
"""

import requests
import pandas as pd
from typing import Dict, List, Optional, Any, Union
import logging
from datetime import datetime, timedelta
import time
from urllib.parse import urljoin
import json
from dataclasses import dataclass
from ..config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class SamsaraAPIConfig:
    """Configuration for PEPMove Samsara API client."""
    api_token: str
    organization_id: str
    group_id: str
    base_url: str = "https://api.samsara.com"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    enable_real_time_tracking: bool = True
    location_update_interval: int = 300


class SamsaraAPIError(Exception):
    """Custom exception for Samsara API errors."""
    pass


class SamsaraAPIClient:
    """Enhanced PEPMove Samsara API client with comprehensive error handling and retry logic."""

    def __init__(self, config: Optional[SamsaraAPIConfig] = None):
        """
        Initialize PEPMove Samsara API client.

        Args:
            config: API configuration (uses settings if not provided)
        """
        if config is None:
            config = SamsaraAPIConfig(
                api_token=settings.samsara.api_token,
                organization_id=settings.samsara.organization_id,
                group_id=settings.samsara.group_id,
                base_url=settings.samsara.base_url,
                timeout=settings.samsara.api_timeout,
                max_retries=settings.samsara.max_retries,
                enable_real_time_tracking=settings.samsara.enable_real_time_tracking,
                location_update_interval=settings.samsara.location_update_interval
            )

        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {config.api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

        logger.info(f"Initialized PEPMove Samsara API client for Organization {config.organization_id}, Group {config.group_id}")

    def _add_pepmove_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add PEPMove-specific parameters to API requests."""
        pepmove_params = params.copy()

        # Add organization and group context where applicable
        if 'groupIds' not in pepmove_params:
            pepmove_params['groupIds'] = [self.config.group_id]

        return pepmove_params
    
    def get_fleet_trips(
        self,
        start_time: datetime,
        end_time: datetime,
        driver_ids: Optional[List[str]] = None,
        vehicle_ids: Optional[List[str]] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get fleet trips data from Samsara API.
        
        Args:
            start_time: Start time for trip data
            end_time: End time for trip data
            driver_ids: Optional list of driver IDs to filter
            vehicle_ids: Optional list of vehicle IDs to filter
            limit: Maximum number of trips to return per request
            
        Returns:
            List of trip dictionaries
        """
        endpoint = "/fleet/trips"
        params = {
            'startTime': start_time.isoformat(),
            'endTime': end_time.isoformat(),
            'limit': limit
        }

        if driver_ids:
            params['driverIds'] = ','.join(driver_ids)
        if vehicle_ids:
            params['vehicleIds'] = ','.join(vehicle_ids)

        # Add PEPMove-specific parameters
        params = self._add_pepmove_params(params)

        return self._paginated_request(endpoint, params)
    
    def get_driver_stats(
        self,
        start_time: datetime,
        end_time: datetime,
        driver_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get driver statistics from Samsara API.
        
        Args:
            start_time: Start time for stats
            end_time: End time for stats
            driver_ids: Optional list of driver IDs to filter
            
        Returns:
            List of driver statistics dictionaries
        """
        endpoint = "/fleet/drivers/stats"
        params = {
            'startTime': start_time.isoformat(),
            'endTime': end_time.isoformat()
        }
        
        if driver_ids:
            params['driverIds'] = ','.join(driver_ids)
        
        return self._paginated_request(endpoint, params)
    
    def get_vehicle_stats(
        self,
        start_time: datetime,
        end_time: datetime,
        vehicle_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get vehicle statistics from Samsara API.
        
        Args:
            start_time: Start time for stats
            end_time: End time for stats
            vehicle_ids: Optional list of vehicle IDs to filter
            
        Returns:
            List of vehicle statistics dictionaries
        """
        endpoint = "/fleet/vehicles/stats"
        params = {
            'startTime': start_time.isoformat(),
            'endTime': end_time.isoformat()
        }
        
        if vehicle_ids:
            params['vehicleIds'] = ','.join(vehicle_ids)
        
        return self._paginated_request(endpoint, params)
    
    def get_drivers(self) -> List[Dict[str, Any]]:
        """
        Get list of drivers from Samsara API.
        
        Returns:
            List of driver dictionaries
        """
        endpoint = "/fleet/drivers"
        return self._paginated_request(endpoint, {})
    
    def get_vehicles(self) -> List[Dict[str, Any]]:
        """
        Get list of vehicles from Samsara API.

        Returns:
            List of vehicle dictionaries
        """
        endpoint = "/fleet/vehicles"
        params = self._add_pepmove_params({})
        return self._paginated_request(endpoint, params)

    # PEPMove-specific API endpoints

    def get_vehicle_locations(
        self,
        vehicle_ids: Optional[List[str]] = None,
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get current vehicle locations for PEPMove fleet.

        Args:
            vehicle_ids: Optional list of vehicle IDs to filter
            include_inactive: Whether to include inactive vehicles

        Returns:
            List of vehicle location dictionaries
        """
        endpoint = "/fleet/vehicles/locations"
        params = {
            'includeInactive': include_inactive
        }

        if vehicle_ids:
            params['vehicleIds'] = ','.join(vehicle_ids)

        params = self._add_pepmove_params(params)
        return self._paginated_request(endpoint, params)

    def get_vehicle_locations_history(
        self,
        start_time: datetime,
        end_time: datetime,
        vehicle_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get historical vehicle locations for PEPMove fleet.

        Args:
            start_time: Start time for location history
            end_time: End time for location history
            vehicle_ids: Optional list of vehicle IDs to filter

        Returns:
            List of historical location dictionaries
        """
        endpoint = "/fleet/vehicles/locations/history"
        params = {
            'startTime': start_time.isoformat(),
            'endTime': end_time.isoformat()
        }

        if vehicle_ids:
            params['vehicleIds'] = ','.join(vehicle_ids)

        params = self._add_pepmove_params(params)
        return self._paginated_request(endpoint, params)

    def get_addresses(self) -> List[Dict[str, Any]]:
        """
        Get all addresses configured for PEPMove organization.

        Returns:
            List of address dictionaries
        """
        endpoint = "/addresses"
        params = self._add_pepmove_params({})
        return self._paginated_request(endpoint, params)

    def create_address(
        self,
        name: str,
        formatted_address: str,
        latitude: float,
        longitude: float,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new address for PEPMove organization.

        Args:
            name: Address name
            formatted_address: Full formatted address
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            notes: Optional notes
            tags: Optional tags for categorization

        Returns:
            Created address dictionary
        """
        endpoint = "/addresses"

        address_data = {
            'name': name,
            'formattedAddress': formatted_address,
            'geofence': {
                'circle': {
                    'radiusMeters': 100,  # Default 100m radius
                    'latitude': latitude,
                    'longitude': longitude
                }
            }
        }

        if notes:
            address_data['notes'] = notes
        if tags:
            address_data['tags'] = tags

        return self._make_post_request(endpoint, address_data)

    def get_real_time_vehicle_stats(
        self,
        vehicle_ids: Optional[List[str]] = None,
        stat_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get real-time vehicle statistics for PEPMove fleet.

        Args:
            vehicle_ids: Optional list of vehicle IDs to filter
            stat_types: Optional list of stat types (e.g., 'engineStates', 'fuelPercentages')

        Returns:
            List of real-time vehicle statistics
        """
        endpoint = "/fleet/vehicles/stats"
        params = {}

        if vehicle_ids:
            params['vehicleIds'] = ','.join(vehicle_ids)
        if stat_types:
            params['types'] = ','.join(stat_types)

        params = self._add_pepmove_params(params)
        return self._paginated_request(endpoint, params)

    def get_routes(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        driver_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get routes for PEPMove fleet.

        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter
            driver_ids: Optional list of driver IDs to filter

        Returns:
            List of route dictionaries
        """
        endpoint = "/fleet/routes"
        params = {}

        if start_time:
            params['startTime'] = start_time.isoformat()
        if end_time:
            params['endTime'] = end_time.isoformat()
        if driver_ids:
            params['driverIds'] = ','.join(driver_ids)

        params = self._add_pepmove_params(params)
        return self._paginated_request(endpoint, params)

    def create_route(
        self,
        name: str,
        driver_id: str,
        vehicle_id: str,
        waypoints: List[Dict[str, Any]],
        start_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Create a new route for PEPMove operations.

        Args:
            name: Route name
            driver_id: Assigned driver ID
            vehicle_id: Assigned vehicle ID
            waypoints: List of waypoint dictionaries with address info
            start_time: Optional scheduled start time

        Returns:
            Created route dictionary
        """
        endpoint = "/fleet/routes"

        route_data = {
            'name': name,
            'driverId': driver_id,
            'vehicleId': vehicle_id,
            'waypoints': waypoints
        }

        if start_time:
            route_data['startTime'] = start_time.isoformat()

        return self._make_post_request(endpoint, route_data)

    def get_pepmove_fleet_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of PEPMove's fleet status.

        Returns:
            Dictionary containing fleet summary information
        """
        try:
            # Get vehicles in PEPMove group
            vehicles = self.get_vehicles()

            # Get current locations
            locations = self.get_vehicle_locations()

            # Get real-time stats
            stats = self.get_real_time_vehicle_stats()

            # Compile summary
            summary = {
                'organization_id': self.config.organization_id,
                'group_id': self.config.group_id,
                'total_vehicles': len(vehicles),
                'vehicles_with_location': len(locations),
                'vehicles_with_stats': len(stats),
                'timestamp': datetime.now().isoformat(),
                'vehicles': vehicles,
                'locations': locations,
                'stats': stats
            }

            logger.info(f"Generated PEPMove fleet summary: {summary['total_vehicles']} vehicles")
            return summary

        except Exception as e:
            logger.error(f"Failed to generate PEPMove fleet summary: {str(e)}")
            raise SamsaraAPIError(f"Fleet summary generation failed: {str(e)}") from e
    
    def _paginated_request(
        self,
        endpoint: str,
        params: Dict[str, Any],
        max_pages: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Make paginated requests to Samsara API.
        
        Args:
            endpoint: API endpoint
            params: Request parameters
            max_pages: Maximum number of pages to fetch
            
        Returns:
            List of all data from paginated responses
        """
        all_data = []
        page = 1
        
        while page <= max_pages:
            current_params = params.copy()
            if page > 1:
                current_params['page'] = page
            
            try:
                response_data = self._make_request(endpoint, current_params)
                data = response_data.get('data', [])
                
                if not data:
                    break
                
                all_data.extend(data)
                
                # Check if there are more pages
                pagination = response_data.get('pagination', {})
                if not pagination.get('hasNextPage', False):
                    break
                
                page += 1
                
                # Rate limiting - be respectful to the API
                time.sleep(0.1)
                
            except SamsaraAPIError as e:
                logger.error(f"Error fetching page {page}: {str(e)}")
                break
        
        logger.info(f"Fetched {len(all_data)} records from {endpoint}")
        return all_data
    
    def _make_request(
        self,
        endpoint: str,
        params: Dict[str, Any],
        method: str = 'GET'
    ) -> Dict[str, Any]:
        """
        Make a single request to Samsara API with retry logic.

        Args:
            endpoint: API endpoint
            params: Request parameters
            method: HTTP method (GET, POST, PUT, DELETE)

        Returns:
            Response data as dictionary
        """
        url = urljoin(self.config.base_url, endpoint)

        for attempt in range(self.config.max_retries + 1):
            try:
                logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")

                if method.upper() == 'GET':
                    response = self.session.get(
                        url,
                        params=params,
                        timeout=self.config.timeout
                    )
                elif method.upper() == 'POST':
                    response = self.session.post(
                        url,
                        json=params,
                        timeout=self.config.timeout
                    )
                else:
                    raise SamsaraAPIError(f"Unsupported HTTP method: {method}")

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                if attempt == self.config.max_retries:
                    error_msg = f"Failed to make {method} request to {url} after {self.config.max_retries + 1} attempts: {str(e)}"
                    logger.error(error_msg)
                    raise SamsaraAPIError(error_msg) from e

                wait_time = self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {str(e)}")
                time.sleep(wait_time)

        raise SamsaraAPIError(f"Unexpected error in request retry logic for {url}")

    def _make_post_request(
        self,
        endpoint: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make a POST request to Samsara API.

        Args:
            endpoint: API endpoint
            data: Request data

        Returns:
            Response data as dictionary
        """
        return self._make_request(endpoint, data, method='POST')


def create_samsara_client() -> SamsaraAPIClient:
    """
    Create a PEPMove Samsara API client using configuration from settings.

    Returns:
        Configured SamsaraAPIClient instance for PEPMove (Org: 5005620, Group: 129031)
    """
    config = SamsaraAPIConfig(
        api_token=settings.samsara.api_token,
        organization_id=settings.samsara.organization_id,
        group_id=settings.samsara.group_id,
        base_url=settings.samsara.base_url,
        timeout=settings.samsara.api_timeout,
        max_retries=settings.samsara.max_retries,
        enable_real_time_tracking=settings.samsara.enable_real_time_tracking,
        location_update_interval=settings.samsara.location_update_interval
    )

    return SamsaraAPIClient(config)


def trips_to_dataframe(trips_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert Samsara trips data to pandas DataFrame.
    
    Args:
        trips_data: List of trip dictionaries from Samsara API
        
    Returns:
        pandas.DataFrame with standardized column names
    """
    if not trips_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(trips_data)
    
    # Standardize column names
    column_mapping = {
        'id': 'trip_id',
        'driverId': 'driver_id',
        'vehicleId': 'vehicle_id',
        'startTime': 'trip_start_time',
        'endTime': 'trip_end_time',
        'distanceMiles': 'total_miles',
        'idleTimeMs': 'idle_time_ms',
        'fuelUsedMl': 'fuel_used_ml',
        'driverName': 'driver_name'
    }
    
    # Rename columns that exist
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            df = df.rename(columns={old_name: new_name})
    
    # Convert timestamps
    timestamp_columns = ['trip_start_time', 'trip_end_time']
    for col in timestamp_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    
    # Extract trip date from start time
    if 'trip_start_time' in df.columns:
        df['trip_date'] = df['trip_start_time'].dt.date
    
    # Convert idle time from milliseconds to minutes
    if 'idle_time_ms' in df.columns:
        df['idle_time'] = df['idle_time_ms'] / (1000 * 60)
    
    # Convert fuel from ml to gallons
    if 'fuel_used_ml' in df.columns:
        df['fuel_used'] = df['fuel_used_ml'] / 3785.41
    
    return df


def driver_stats_to_dataframe(stats_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert Samsara driver stats data to pandas DataFrame.
    
    Args:
        stats_data: List of driver statistics dictionaries from Samsara API
        
    Returns:
        pandas.DataFrame with standardized column names
    """
    if not stats_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(stats_data)
    
    # Standardize column names
    column_mapping = {
        'driverId': 'driver_id',
        'driverName': 'driver_name',
        'totalDistanceMiles': 'total_miles',
        'totalIdleTimeMs': 'idle_time_ms',
        'totalDrivingTimeMs': 'driving_time_ms',
        'totalEngineHours': 'engine_hours'
    }
    
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            df = df.rename(columns={old_name: new_name})
    
    # Convert time fields from milliseconds to minutes
    time_fields = ['idle_time_ms', 'driving_time_ms']
    for field in time_fields:
        if field in df.columns:
            new_field = field.replace('_ms', '')
            df[new_field] = df[field] / (1000 * 60)
    
    return df


def vehicle_locations_to_dataframe(locations_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert Samsara vehicle locations data to pandas DataFrame.

    Args:
        locations_data: List of vehicle location dictionaries from Samsara API

    Returns:
        pandas.DataFrame with standardized column names for PEPMove
    """
    if not locations_data:
        return pd.DataFrame()

    df = pd.DataFrame(locations_data)

    # Standardize column names
    column_mapping = {
        'vehicleId': 'vehicle_id',
        'latitude': 'latitude',
        'longitude': 'longitude',
        'time': 'timestamp',
        'speed': 'speed_mph',
        'heading': 'heading_degrees',
        'address': 'formatted_address'
    }

    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            df = df.rename(columns={old_name: new_name})

    # Convert timestamp
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Add PEPMove context
    df['organization_id'] = '5005620'
    df['group_id'] = '129031'

    return df


def addresses_to_dataframe(addresses_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert Samsara addresses data to pandas DataFrame.

    Args:
        addresses_data: List of address dictionaries from Samsara API

    Returns:
        pandas.DataFrame with standardized column names for PEPMove
    """
    if not addresses_data:
        return pd.DataFrame()

    df = pd.DataFrame(addresses_data)

    # Standardize column names
    column_mapping = {
        'id': 'address_id',
        'name': 'address_name',
        'formattedAddress': 'formatted_address',
        'notes': 'notes',
        'tags': 'tags'
    }

    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            df = df.rename(columns={old_name: new_name})

    # Extract geofence information if available
    if 'geofence' in df.columns:
        df['latitude'] = df['geofence'].apply(
            lambda x: x.get('circle', {}).get('latitude') if isinstance(x, dict) else None
        )
        df['longitude'] = df['geofence'].apply(
            lambda x: x.get('circle', {}).get('longitude') if isinstance(x, dict) else None
        )
        df['radius_meters'] = df['geofence'].apply(
            lambda x: x.get('circle', {}).get('radiusMeters') if isinstance(x, dict) else None
        )

    # Add PEPMove context
    df['organization_id'] = '5005620'
    df['group_id'] = '129031'

    return df


def routes_to_dataframe(routes_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert Samsara routes data to pandas DataFrame.

    Args:
        routes_data: List of route dictionaries from Samsara API

    Returns:
        pandas.DataFrame with standardized column names for PEPMove
    """
    if not routes_data:
        return pd.DataFrame()

    df = pd.DataFrame(routes_data)

    # Standardize column names
    column_mapping = {
        'id': 'route_id',
        'name': 'route_name',
        'driverId': 'driver_id',
        'vehicleId': 'vehicle_id',
        'startTime': 'start_time',
        'endTime': 'end_time',
        'status': 'route_status'
    }

    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            df = df.rename(columns={old_name: new_name})

    # Convert timestamps
    timestamp_columns = ['start_time', 'end_time']
    for col in timestamp_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])

    # Extract waypoint count if available
    if 'waypoints' in df.columns:
        df['waypoint_count'] = df['waypoints'].apply(
            lambda x: len(x) if isinstance(x, list) else 0
        )

    # Add PEPMove context
    df['organization_id'] = '5005620'
    df['group_id'] = '129031'

    return df
