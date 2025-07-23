"""
Tests for Samsara API integration.

This module tests the Samsara API client functionality including:
- API authentication and connection
- Data fetching and formatting
- Error handling and retry logic
- Integration with the enrichment pipeline
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import requests
from requests.exceptions import RequestException, Timeout

from ..utils.samsara_api import (
    SamsaraAPIClient,
    SamsaraAPIConfig,
    SamsaraAPIError,
    trips_to_dataframe,
    driver_stats_to_dataframe,
    vehicle_locations_to_dataframe,
    addresses_to_dataframe,
    routes_to_dataframe,
    create_samsara_client
)
from ..core.samsara_enrichment import load_samsara_data, SamsaraAPIClient as EnrichmentAPIClient


class TestSamsaraAPIConfig:
    """Test SamsaraAPIConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = SamsaraAPIConfig(
            api_token="test_token",
            organization_id="5005620",
            group_id="129031"
        )

        assert config.api_token == "test_token"
        assert config.organization_id == "5005620"
        assert config.group_id == "129031"
        assert config.base_url == "https://api.samsara.com"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.enable_real_time_tracking == True
        assert config.location_update_interval == 300


class TestSamsaraAPIClient:
    """Test SamsaraAPIClient functionality."""
    
    @pytest.fixture
    def api_config(self):
        """Create test API configuration."""
        return SamsaraAPIConfig(
            api_token="test_token_7qCpNNFjxM5S4jojGWzO9vxciB8o8I",
            base_url="https://api.samsara.com",
            timeout=10,
            max_retries=2
        )
    
    @pytest.fixture
    def api_client(self, api_config):
        """Create test API client."""
        return SamsaraAPIClient(api_config)
    
    def test_client_initialization(self, api_client, api_config):
        """Test API client initialization."""
        assert api_client.config == api_config
        assert api_client.session.headers['Authorization'] == f'Bearer {api_config.api_token}'
        assert api_client.session.headers['Content-Type'] == 'application/json'
    
    @patch('requests.Session.get')
    def test_get_fleet_trips_success(self, mock_get, api_client):
        """Test successful fleet trips API call."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'id': 'trip_123',
                    'driverId': 'driver_456',
                    'vehicleId': 'vehicle_789',
                    'startTime': '2024-01-15T08:00:00Z',
                    'endTime': '2024-01-15T16:00:00Z',
                    'distanceMiles': 150.5,
                    'idleTimeMs': 1800000,  # 30 minutes
                    'fuelUsedMl': 15000
                }
            ],
            'pagination': {'hasNextPage': False}
        }
        mock_get.return_value = mock_response
        
        # Test API call
        start_time = datetime(2024, 1, 15)
        end_time = datetime(2024, 1, 16)
        
        result = api_client.get_fleet_trips(start_time, end_time)
        
        assert len(result) == 1
        assert result[0]['id'] == 'trip_123'
        assert result[0]['distanceMiles'] == 150.5
        
        # Verify API call parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert 'startTime' in call_args[1]['params']
        assert 'endTime' in call_args[1]['params']
    
    @patch('requests.Session.get')
    def test_get_fleet_trips_with_filters(self, mock_get, api_client):
        """Test fleet trips API call with driver and vehicle filters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': [], 'pagination': {'hasNextPage': False}}
        mock_get.return_value = mock_response
        
        start_time = datetime(2024, 1, 15)
        end_time = datetime(2024, 1, 16)
        driver_ids = ['driver_1', 'driver_2']
        vehicle_ids = ['vehicle_1', 'vehicle_2']
        
        api_client.get_fleet_trips(start_time, end_time, driver_ids, vehicle_ids)
        
        call_args = mock_get.call_args
        params = call_args[1]['params']
        assert params['driverIds'] == 'driver_1,driver_2'
        assert params['vehicleIds'] == 'vehicle_1,vehicle_2'
    
    @patch('requests.Session.get')
    def test_api_retry_logic(self, mock_get, api_client):
        """Test API retry logic on failure."""
        # First call fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.side_effect = RequestException("Connection error")
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {'data': [], 'pagination': {'hasNextPage': False}}
        
        mock_get.side_effect = [RequestException("Connection error"), mock_response_success]
        
        start_time = datetime(2024, 1, 15)
        end_time = datetime(2024, 1, 16)
        
        result = api_client.get_fleet_trips(start_time, end_time)
        
        assert result == []
        assert mock_get.call_count == 2
    
    @patch('requests.Session.get')
    def test_api_rate_limiting(self, mock_get, api_client):
        """Test API rate limiting handling."""
        # First call gets rate limited, second succeeds
        mock_response_rate_limited = Mock()
        mock_response_rate_limited.status_code = 429
        mock_response_rate_limited.headers = {'Retry-After': '1'}
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {'data': [], 'pagination': {'hasNextPage': False}}
        
        mock_get.side_effect = [mock_response_rate_limited, mock_response_success]
        
        start_time = datetime(2024, 1, 15)
        end_time = datetime(2024, 1, 16)
        
        with patch('time.sleep') as mock_sleep:
            result = api_client.get_fleet_trips(start_time, end_time)
            mock_sleep.assert_called_with(1)  # Should sleep for Retry-After duration
        
        assert result == []
        assert mock_get.call_count == 2
    
    @patch('requests.Session.get')
    def test_api_max_retries_exceeded(self, mock_get, api_client):
        """Test behavior when max retries are exceeded."""
        mock_get.side_effect = RequestException("Persistent error")
        
        start_time = datetime(2024, 1, 15)
        end_time = datetime(2024, 1, 16)
        
        with pytest.raises(SamsaraAPIError) as exc_info:
            api_client.get_fleet_trips(start_time, end_time)
        
        assert "Failed to make request" in str(exc_info.value)
        assert mock_get.call_count == api_client.config.max_retries + 1


class TestDataFormatting:
    """Test data formatting functions."""
    
    def test_trips_to_dataframe(self):
        """Test conversion of trips data to DataFrame."""
        trips_data = [
            {
                'id': 'trip_123',
                'driverId': 'driver_456',
                'vehicleId': 'vehicle_789',
                'startTime': '2024-01-15T08:00:00Z',
                'endTime': '2024-01-15T16:00:00Z',
                'distanceMiles': 150.5,
                'idleTimeMs': 1800000,  # 30 minutes
                'fuelUsedMl': 15000,
                'driverName': 'John Doe'
            }
        ]
        
        df = trips_to_dataframe(trips_data)
        
        assert len(df) == 1
        assert 'trip_id' in df.columns
        assert 'driver_id' in df.columns
        assert 'total_miles' in df.columns
        assert 'idle_time' in df.columns
        assert 'fuel_used' in df.columns
        assert 'trip_date' in df.columns
        
        # Check data conversion
        assert df.iloc[0]['trip_id'] == 'trip_123'
        assert df.iloc[0]['total_miles'] == 150.5
        assert df.iloc[0]['idle_time'] == 30.0  # Converted from ms to minutes
        assert abs(df.iloc[0]['fuel_used'] - 3.96) < 0.01  # Converted from ml to gallons
    
    def test_trips_to_dataframe_empty(self):
        """Test conversion of empty trips data."""
        df = trips_to_dataframe([])
        assert df.empty
        assert isinstance(df, pd.DataFrame)
    
    def test_driver_stats_to_dataframe(self):
        """Test conversion of driver stats data to DataFrame."""
        stats_data = [
            {
                'driverId': 'driver_456',
                'driverName': 'John Doe',
                'totalDistanceMiles': 500.0,
                'totalIdleTimeMs': 3600000,  # 60 minutes
                'totalDrivingTimeMs': 14400000,  # 240 minutes
                'totalEngineHours': 5.0
            }
        ]
        
        df = driver_stats_to_dataframe(stats_data)
        
        assert len(df) == 1
        assert 'driver_id' in df.columns
        assert 'driver_name' in df.columns
        assert 'total_miles' in df.columns
        assert 'idle_time' in df.columns
        assert 'driving_time' in df.columns
        
        # Check data conversion
        assert df.iloc[0]['driver_id'] == 'driver_456'
        assert df.iloc[0]['total_miles'] == 500.0
        assert df.iloc[0]['idle_time'] == 60.0  # Converted from ms to minutes
        assert df.iloc[0]['driving_time'] == 240.0  # Converted from ms to minutes


class TestSamsaraEnrichmentIntegration:
    """Test integration with the enrichment module."""
    
    @patch('pepworkday_pipeline.utils.samsara_api.create_samsara_client')
    def test_load_samsara_data_from_api(self, mock_create_client):
        """Test loading Samsara data via API in enrichment module."""
        # Mock API client
        mock_client = Mock()
        mock_client.get_trips_data.return_value = pd.DataFrame([
            {
                'trip_id': 'trip_123',
                'driver_id': 'driver_456',
                'trip_date': datetime(2024, 1, 15),
                'total_miles': 150.5,
                'idle_time': 30.0
            }
        ])
        mock_create_client.return_value = mock_client
        
        # Test API loading
        start_date = datetime(2024, 1, 15)
        end_date = datetime(2024, 1, 16)
        
        result_df = load_samsara_data(
            api_client=mock_client,
            start_date=start_date,
            end_date=end_date
        )
        
        assert len(result_df) == 1
        assert 'trip_id' in result_df.columns
        assert 'driver_id' in result_df.columns
    
    def test_load_samsara_data_validation(self):
        """Test validation in load_samsara_data function."""
        # Test missing both file and API client
        with pytest.raises(Exception) as exc_info:
            load_samsara_data()
        assert "Must provide either file_path or api_client" in str(exc_info.value)
        
        # Test providing both file and API client
        mock_client = Mock()
        with pytest.raises(Exception) as exc_info:
            load_samsara_data(file_path="test.csv", api_client=mock_client)
        assert "Provide either file_path or api_client, not both" in str(exc_info.value)


@patch('pepworkday_pipeline.config.settings.settings')
def test_create_samsara_client(mock_settings):
    """Test creation of Samsara client from settings."""
    # Mock settings
    mock_settings.samsara.api_token = "samsara_api_7qCpNNFjxM5S4jojGWzO9vxciB8o8I"
    mock_settings.samsara.base_url = "https://api.samsara.com"
    mock_settings.samsara.api_timeout = 30
    mock_settings.samsara.max_retries = 3
    
    client = create_samsara_client()

    assert isinstance(client, SamsaraAPIClient)
    assert client.config.api_token == "samsara_api_7qCpNNFjxM5S4jojGWzO9vxciB8o8I"
    assert client.config.organization_id == "5005620"
    assert client.config.group_id == "129031"


class TestPEPMoveSpecificEndpoints:
    """Test PEPMove-specific Samsara API endpoints."""

    @pytest.fixture
    def pepmove_api_config(self):
        """Create PEPMove API configuration."""
        return SamsaraAPIConfig(
            api_token="samsara_api_7qCpNNFjxM5S4jojGWzO9vxciB8o8I",
            organization_id="5005620",
            group_id="129031",
            base_url="https://api.samsara.com",
            timeout=10,
            max_retries=2
        )

    @pytest.fixture
    def pepmove_api_client(self, pepmove_api_config):
        """Create PEPMove API client."""
        return SamsaraAPIClient(pepmove_api_config)

    @patch('requests.Session.get')
    def test_get_vehicle_locations(self, mock_get, pepmove_api_client):
        """Test getting vehicle locations for PEPMove fleet."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'vehicleId': 'vehicle_123',
                    'latitude': 40.7128,
                    'longitude': -74.0060,
                    'time': '2024-01-15T12:00:00Z',
                    'speed': 35.5,
                    'heading': 180,
                    'address': '123 Main St, New York, NY'
                }
            ],
            'pagination': {'hasNextPage': False}
        }
        mock_get.return_value = mock_response

        result = pepmove_api_client.get_vehicle_locations()

        assert len(result) == 1
        assert result[0]['vehicleId'] == 'vehicle_123'
        assert result[0]['latitude'] == 40.7128

        # Verify PEPMove parameters were added
        call_args = mock_get.call_args
        params = call_args[1]['params']
        assert 'groupIds' in params
        assert params['groupIds'] == ['129031']

    @patch('requests.Session.get')
    def test_get_addresses(self, mock_get, pepmove_api_client):
        """Test getting addresses for PEPMove organization."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'id': 'addr_123',
                    'name': 'PEPMove Depot',
                    'formattedAddress': '123 Depot St, City, ST 12345',
                    'geofence': {
                        'circle': {
                            'latitude': 40.7128,
                            'longitude': -74.0060,
                            'radiusMeters': 100
                        }
                    },
                    'notes': 'Main depot location',
                    'tags': ['depot', 'pepmove']
                }
            ],
            'pagination': {'hasNextPage': False}
        }
        mock_get.return_value = mock_response

        result = pepmove_api_client.get_addresses()

        assert len(result) == 1
        assert result[0]['name'] == 'PEPMove Depot'
        assert result[0]['formattedAddress'] == '123 Depot St, City, ST 12345'

    @patch('requests.Session.post')
    def test_create_address(self, mock_post, pepmove_api_client):
        """Test creating a new address for PEPMove."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': 'addr_new_123',
            'name': 'New Customer Location',
            'formattedAddress': '456 Customer Ave, City, ST 12345'
        }
        mock_post.return_value = mock_response

        result = pepmove_api_client.create_address(
            name="New Customer Location",
            formatted_address="456 Customer Ave, City, ST 12345",
            latitude=40.7589,
            longitude=-73.9851,
            notes="New customer delivery point",
            tags=["customer", "delivery"]
        )

        assert result['name'] == 'New Customer Location'
        assert result['id'] == 'addr_new_123'

        # Verify POST request was made with correct data
        call_args = mock_post.call_args
        request_data = call_args[1]['json']
        assert request_data['name'] == 'New Customer Location'
        assert request_data['formattedAddress'] == '456 Customer Ave, City, ST 12345'
        assert request_data['notes'] == 'New customer delivery point'
        assert request_data['tags'] == ['customer', 'delivery']

    @patch('requests.Session.get')
    def test_get_pepmove_fleet_summary(self, mock_get, pepmove_api_client):
        """Test getting comprehensive PEPMove fleet summary."""
        # Mock multiple API calls for fleet summary
        mock_responses = [
            # Vehicles response
            Mock(status_code=200, json=lambda: {
                'data': [{'id': 'v1'}, {'id': 'v2'}],
                'pagination': {'hasNextPage': False}
            }),
            # Locations response
            Mock(status_code=200, json=lambda: {
                'data': [{'vehicleId': 'v1', 'latitude': 40.7128}],
                'pagination': {'hasNextPage': False}
            }),
            # Stats response
            Mock(status_code=200, json=lambda: {
                'data': [{'vehicleId': 'v1', 'engineState': 'Running'}],
                'pagination': {'hasNextPage': False}
            })
        ]
        mock_get.side_effect = mock_responses

        result = pepmove_api_client.get_pepmove_fleet_summary()

        assert result['organization_id'] == '5005620'
        assert result['group_id'] == '129031'
        assert result['total_vehicles'] == 2
        assert result['vehicles_with_location'] == 1
        assert result['vehicles_with_stats'] == 1
        assert 'timestamp' in result


class TestPEPMoveDataFormatting:
    """Test PEPMove-specific data formatting functions."""

    def test_vehicle_locations_to_dataframe(self):
        """Test conversion of vehicle locations to DataFrame."""
        locations_data = [
            {
                'vehicleId': 'vehicle_123',
                'latitude': 40.7128,
                'longitude': -74.0060,
                'time': '2024-01-15T12:00:00Z',
                'speed': 35.5,
                'heading': 180,
                'address': '123 Main St, New York, NY'
            }
        ]

        df = vehicle_locations_to_dataframe(locations_data)

        assert len(df) == 1
        assert 'vehicle_id' in df.columns
        assert 'latitude' in df.columns
        assert 'longitude' in df.columns
        assert 'timestamp' in df.columns
        assert 'organization_id' in df.columns
        assert 'group_id' in df.columns

        # Check PEPMove context
        assert df.iloc[0]['organization_id'] == '5005620'
        assert df.iloc[0]['group_id'] == '129031'
        assert df.iloc[0]['vehicle_id'] == 'vehicle_123'

    def test_addresses_to_dataframe(self):
        """Test conversion of addresses to DataFrame."""
        addresses_data = [
            {
                'id': 'addr_123',
                'name': 'PEPMove Depot',
                'formattedAddress': '123 Depot St, City, ST 12345',
                'geofence': {
                    'circle': {
                        'latitude': 40.7128,
                        'longitude': -74.0060,
                        'radiusMeters': 100
                    }
                },
                'notes': 'Main depot',
                'tags': ['depot']
            }
        ]

        df = addresses_to_dataframe(addresses_data)

        assert len(df) == 1
        assert 'address_id' in df.columns
        assert 'address_name' in df.columns
        assert 'formatted_address' in df.columns
        assert 'latitude' in df.columns
        assert 'longitude' in df.columns
        assert 'radius_meters' in df.columns
        assert 'organization_id' in df.columns
        assert 'group_id' in df.columns

        # Check data extraction
        assert df.iloc[0]['address_id'] == 'addr_123'
        assert df.iloc[0]['address_name'] == 'PEPMove Depot'
        assert df.iloc[0]['latitude'] == 40.7128
        assert df.iloc[0]['longitude'] == -74.0060
        assert df.iloc[0]['radius_meters'] == 100

        # Check PEPMove context
        assert df.iloc[0]['organization_id'] == '5005620'
        assert df.iloc[0]['group_id'] == '129031'
