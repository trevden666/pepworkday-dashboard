#!/usr/bin/env python3
"""
Tests for Google Sheets API client using Application Default Credentials.

This module tests the sheets.py functionality including:
- Authentication via Application Default Credentials
- Basic read/write operations
- Error handling
- Integration with PepWorkday spreadsheet

PepWorkday Configuration:
- Spreadsheet ID: 1e5lulkbbwk6F9Xu97K38f40PUGVdp_f7W9qh31UglcU
- Service Account: pepmove@pepworkday.iam.gserviceaccount.com
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
import logging

# Add the scripts directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

try:
    from sheets import SheetsClient, create_sheets_client, SPREADSHEET_ID, SCOPES
except ImportError as e:
    print(f"Error importing sheets module: {e}")
    sys.exit(1)

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestSheetsClient(unittest.TestCase):
    """Test cases for SheetsClient class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_spreadsheet_id = SPREADSHEET_ID
        self.test_credentials_path = '/path/to/pepmove-service-account.json'
    
    @patch.dict(os.environ, {'GOOGLE_APPLICATION_CREDENTIALS': '/path/to/pepmove-service-account.json'})
    @patch('sheets.service_account.Credentials.from_service_account_file')
    @patch('sheets.build')
    @patch('os.path.exists')
    def test_client_initialization(self, mock_exists, mock_build, mock_creds):
        """Test successful client initialization."""
        # Mock file exists
        mock_exists.return_value = True
        
        # Mock credentials
        mock_credentials = Mock()
        mock_creds.return_value = mock_credentials
        
        # Mock service build
        mock_service = Mock()
        mock_spreadsheet = Mock()
        mock_service.spreadsheets.return_value = mock_spreadsheet
        mock_build.return_value = mock_service
        
        # Create client
        client = SheetsClient(self.test_spreadsheet_id)
        
        # Verify initialization
        self.assertEqual(client.spreadsheet_id, self.test_spreadsheet_id)
        self.assertEqual(client.service, mock_service)
        self.assertEqual(client.spreadsheet, mock_spreadsheet)
        
        # Verify credentials were loaded with correct scopes
        mock_creds.assert_called_once_with(
            self.test_credentials_path,
            scopes=SCOPES
        )
        
        # Verify service was built
        mock_build.assert_called_once_with('sheets', 'v4', credentials=mock_credentials)
    
    def test_missing_credentials_env_var(self):
        """Test error when GOOGLE_APPLICATION_CREDENTIALS is not set."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                SheetsClient(self.test_spreadsheet_id)
            
            self.assertIn("GOOGLE_APPLICATION_CREDENTIALS", str(context.exception))
    
    @patch.dict(os.environ, {'GOOGLE_APPLICATION_CREDENTIALS': '/nonexistent/path.json'})
    @patch('os.path.exists')
    def test_missing_credentials_file(self, mock_exists):
        """Test error when credentials file doesn't exist."""
        mock_exists.return_value = False
        
        with self.assertRaises(FileNotFoundError) as context:
            SheetsClient(self.test_spreadsheet_id)
        
        self.assertIn("/nonexistent/path.json", str(context.exception))
    
    @patch.dict(os.environ, {'GOOGLE_APPLICATION_CREDENTIALS': '/path/to/pepmove-service-account.json'})
    @patch('sheets.service_account.Credentials.from_service_account_file')
    @patch('sheets.build')
    @patch('os.path.exists')
    def test_get_values(self, mock_exists, mock_build, mock_creds):
        """Test getting values from spreadsheet."""
        # Setup mocks
        mock_exists.return_value = True
        mock_credentials = Mock()
        mock_creds.return_value = mock_credentials
        
        mock_service = Mock()
        mock_spreadsheet = Mock()
        mock_values = Mock()
        mock_get = Mock()
        
        mock_service.spreadsheets.return_value = mock_spreadsheet
        mock_spreadsheet.values.return_value = mock_values
        mock_values.get.return_value = mock_get
        
        # Mock API response
        test_values = [['Header1', 'Header2'], ['Value1', 'Value2']]
        mock_get.execute.return_value = {'values': test_values}
        
        mock_build.return_value = mock_service
        
        # Create client and test
        client = SheetsClient(self.test_spreadsheet_id)
        result = client.get_values('RawData!A1:B2')
        
        # Verify result
        self.assertEqual(result, test_values)
        
        # Verify API call
        mock_values.get.assert_called_once_with(
            spreadsheetId=self.test_spreadsheet_id,
            range='RawData!A1:B2'
        )
    
    @patch.dict(os.environ, {'GOOGLE_APPLICATION_CREDENTIALS': '/path/to/pepmove-service-account.json'})
    @patch('sheets.service_account.Credentials.from_service_account_file')
    @patch('sheets.build')
    @patch('os.path.exists')
    def test_update_values(self, mock_exists, mock_build, mock_creds):
        """Test updating values in spreadsheet."""
        # Setup mocks
        mock_exists.return_value = True
        mock_credentials = Mock()
        mock_creds.return_value = mock_credentials
        
        mock_service = Mock()
        mock_spreadsheet = Mock()
        mock_values = Mock()
        mock_update = Mock()
        
        mock_service.spreadsheets.return_value = mock_spreadsheet
        mock_spreadsheet.values.return_value = mock_values
        mock_values.update.return_value = mock_update
        
        # Mock API response
        mock_update.execute.return_value = {'updatedCells': 4}
        
        mock_build.return_value = mock_service
        
        # Create client and test
        client = SheetsClient(self.test_spreadsheet_id)
        test_values = [['New1', 'New2'], ['New3', 'New4']]
        result = client.update_values('RawData!A1:B2', test_values)
        
        # Verify result
        self.assertEqual(result['updatedCells'], 4)
        
        # Verify API call
        mock_values.update.assert_called_once_with(
            spreadsheetId=self.test_spreadsheet_id,
            range='RawData!A1:B2',
            valueInputOption='RAW',
            body={'values': test_values}
        )
    
    @patch.dict(os.environ, {'GOOGLE_APPLICATION_CREDENTIALS': '/path/to/pepmove-service-account.json'})
    @patch('sheets.service_account.Credentials.from_service_account_file')
    @patch('sheets.build')
    @patch('os.path.exists')
    def test_list_worksheets(self, mock_exists, mock_build, mock_creds):
        """Test listing worksheets in spreadsheet."""
        # Setup mocks
        mock_exists.return_value = True
        mock_credentials = Mock()
        mock_creds.return_value = mock_credentials
        
        mock_service = Mock()
        mock_spreadsheet = Mock()
        mock_get = Mock()
        
        mock_service.spreadsheets.return_value = mock_spreadsheet
        mock_spreadsheet.get.return_value = mock_get
        
        # Mock API response
        mock_get.execute.return_value = {
            'properties': {'title': 'PepWorkday Spreadsheet'},
            'sheets': [
                {'properties': {'title': 'RawData'}},
                {'properties': {'title': 'ProcessedData'}},
                {'properties': {'title': 'Summary'}}
            ]
        }
        
        mock_build.return_value = mock_service
        
        # Create client and test
        client = SheetsClient(self.test_spreadsheet_id)
        worksheets = client.list_worksheets()
        
        # Verify result
        expected_worksheets = ['RawData', 'ProcessedData', 'Summary']
        self.assertEqual(worksheets, expected_worksheets)


class TestSheetsIntegration(unittest.TestCase):
    """Integration tests for Sheets client (requires actual credentials)."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        self.skip_integration = not (
            self.credentials_path and 
            os.path.exists(self.credentials_path)
        )
    
    def test_auth(self):
        """Test authentication and basic read operation on RawData!A1."""
        if self.skip_integration:
            self.skipTest("Integration test skipped: GOOGLE_APPLICATION_CREDENTIALS not set or file not found")
        
        try:
            # Create client
            client = create_sheets_client()
            
            # Test basic read operation
            values = client.get_values('RawData!A1')
            
            # Assert that we get a list (even if empty)
            self.assertIsInstance(values, list)
            
            logger.info(f"Successfully read RawData!A1: {values}")
            
        except Exception as e:
            self.fail(f"Authentication test failed: {str(e)}")
    
    def test_spreadsheet_access(self):
        """Test that we can access the PepWorkday spreadsheet."""
        if self.skip_integration:
            self.skipTest("Integration test skipped: GOOGLE_APPLICATION_CREDENTIALS not set or file not found")
        
        try:
            # Create client
            client = create_sheets_client()
            
            # Get spreadsheet info
            info = client.get_spreadsheet_info()
            
            # Verify we can access the spreadsheet
            self.assertIsInstance(info, dict)
            self.assertIn('properties', info)
            
            # Get title
            title = info.get('properties', {}).get('title', '')
            logger.info(f"Successfully accessed spreadsheet: {title}")
            
        except Exception as e:
            self.fail(f"Spreadsheet access test failed: {str(e)}")
    
    def test_worksheet_listing(self):
        """Test listing worksheets in the spreadsheet."""
        if self.skip_integration:
            self.skipTest("Integration test skipped: GOOGLE_APPLICATION_CREDENTIALS not set or file not found")
        
        try:
            # Create client
            client = create_sheets_client()
            
            # List worksheets
            worksheets = client.list_worksheets()
            
            # Verify we get a list of worksheet names
            self.assertIsInstance(worksheets, list)
            
            # Check if RawData worksheet exists (expected for PepWorkday)
            if worksheets:
                logger.info(f"Found worksheets: {worksheets}")
                # Optionally check for expected worksheets
                # self.assertIn('RawData', worksheets)
            
        except Exception as e:
            self.fail(f"Worksheet listing test failed: {str(e)}")


def test_create_sheets_client():
    """Test the create_sheets_client factory function."""
    with patch('sheets.SheetsClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Test with default spreadsheet ID
        result = create_sheets_client()
        mock_client_class.assert_called_once_with(SPREADSHEET_ID)
        assert result == mock_client
        
        # Test with custom spreadsheet ID
        custom_id = 'custom_spreadsheet_id'
        mock_client_class.reset_mock()
        result = create_sheets_client(custom_id)
        mock_client_class.assert_called_once_with(custom_id)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
