#!/usr/bin/env python3
"""
Google Sheets API client using Application Default Credentials.

This module provides a simplified interface to Google Sheets API using
service account authentication via Application Default Credentials.

PepWorkday Configuration:
- Spreadsheet ID: 1e5lulkbbwk6F9Xu97K38f40PUGVdp_f7W9qh31UglcU
- Service Account: pepmove@pepworkday.iam.gserviceaccount.com
- Authentication: Application Default Credentials via GOOGLE_APPLICATION_CREDENTIALS
"""

import os
import logging
from typing import Dict, List, Any, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Sheets API scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# PepWorkday spreadsheet ID
SPREADSHEET_ID = '1e5lulkbbwk6F9Xu97K38f40PUGVdp_f7W9qh31UglcU'


class SheetsClient:
    """Google Sheets API client using Application Default Credentials."""
    
    def __init__(self, spreadsheet_id: str = SPREADSHEET_ID):
        """
        Initialize the Sheets client with Application Default Credentials.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
        """
        self.spreadsheet_id = spreadsheet_id
        self.service = None
        self.spreadsheet = None
        
        # Initialize the client
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Sheets API client with service account credentials."""
        try:
            # Load credentials from service account file
            credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            if not credentials_path:
                raise ValueError(
                    "GOOGLE_APPLICATION_CREDENTIALS environment variable not set. "
                    "Please set it to the path of your service account JSON file."
                )
            
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    f"Service account file not found: {credentials_path}"
                )
            
            logger.info(f"Loading credentials from: {credentials_path}")
            
            # Load service account credentials with required scopes
            creds = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=SCOPES
            )
            
            logger.info("Successfully loaded service account credentials")
            
            # Build the Sheets API service
            self.service = build('sheets', 'v4', credentials=creds)
            self.spreadsheet = self.service.spreadsheets()
            
            logger.info(f"Initialized Google Sheets client for spreadsheet: {self.spreadsheet_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {str(e)}")
            raise
    
    def get_values(self, range_name: str) -> List[List[str]]:
        """
        Get values from a specific range in the spreadsheet.
        
        Args:
            range_name: A1 notation range (e.g., 'RawData!A1:Z100')
            
        Returns:
            List of rows, where each row is a list of cell values
        """
        try:
            logger.info(f"Getting values from range: {range_name}")
            
            result = self.spreadsheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            logger.info(f"Retrieved {len(values)} rows from {range_name}")
            
            return values
            
        except HttpError as e:
            logger.error(f"HTTP error getting values from {range_name}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error getting values from {range_name}: {str(e)}")
            raise
    
    def update_values(
        self, 
        range_name: str, 
        values: List[List[Any]], 
        value_input_option: str = 'RAW'
    ) -> Dict[str, Any]:
        """
        Update values in a specific range of the spreadsheet.
        
        Args:
            range_name: A1 notation range (e.g., 'RawData!A1:Z100')
            values: 2D list of values to write
            value_input_option: How to interpret input ('RAW' or 'USER_ENTERED')
            
        Returns:
            API response dictionary
        """
        try:
            logger.info(f"Updating {len(values)} rows in range: {range_name}")
            
            body = {
                'values': values
            }
            
            result = self.spreadsheet.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body
            ).execute()
            
            updated_cells = result.get('updatedCells', 0)
            logger.info(f"Updated {updated_cells} cells in {range_name}")
            
            return result
            
        except HttpError as e:
            logger.error(f"HTTP error updating values in {range_name}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error updating values in {range_name}: {str(e)}")
            raise
    
    def append_values(
        self, 
        range_name: str, 
        values: List[List[Any]], 
        value_input_option: str = 'RAW'
    ) -> Dict[str, Any]:
        """
        Append values to the end of a range in the spreadsheet.
        
        Args:
            range_name: A1 notation range (e.g., 'RawData!A:Z')
            values: 2D list of values to append
            value_input_option: How to interpret input ('RAW' or 'USER_ENTERED')
            
        Returns:
            API response dictionary
        """
        try:
            logger.info(f"Appending {len(values)} rows to range: {range_name}")
            
            body = {
                'values': values
            }
            
            result = self.spreadsheet.values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body
            ).execute()
            
            updated_cells = result.get('updates', {}).get('updatedCells', 0)
            logger.info(f"Appended {updated_cells} cells to {range_name}")
            
            return result
            
        except HttpError as e:
            logger.error(f"HTTP error appending values to {range_name}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error appending values to {range_name}: {str(e)}")
            raise
    
    def clear_values(self, range_name: str) -> Dict[str, Any]:
        """
        Clear values in a specific range of the spreadsheet.
        
        Args:
            range_name: A1 notation range (e.g., 'RawData!A1:Z100')
            
        Returns:
            API response dictionary
        """
        try:
            logger.info(f"Clearing values in range: {range_name}")
            
            result = self.spreadsheet.values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            logger.info(f"Cleared values in {range_name}")
            return result
            
        except HttpError as e:
            logger.error(f"HTTP error clearing values in {range_name}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error clearing values in {range_name}: {str(e)}")
            raise
    
    def get_spreadsheet_info(self) -> Dict[str, Any]:
        """
        Get information about the spreadsheet.
        
        Returns:
            Spreadsheet metadata dictionary
        """
        try:
            logger.info("Getting spreadsheet information")
            
            result = self.spreadsheet.get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            title = result.get('properties', {}).get('title', 'Unknown')
            sheet_count = len(result.get('sheets', []))
            
            logger.info(f"Spreadsheet: {title} ({sheet_count} sheets)")
            
            return result
            
        except HttpError as e:
            logger.error(f"HTTP error getting spreadsheet info: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error getting spreadsheet info: {str(e)}")
            raise
    
    def list_worksheets(self) -> List[str]:
        """
        Get list of worksheet names in the spreadsheet.
        
        Returns:
            List of worksheet names
        """
        try:
            spreadsheet_info = self.get_spreadsheet_info()
            worksheets = []
            
            for sheet in spreadsheet_info.get('sheets', []):
                sheet_name = sheet.get('properties', {}).get('title', '')
                if sheet_name:
                    worksheets.append(sheet_name)
            
            logger.info(f"Found {len(worksheets)} worksheets: {worksheets}")
            return worksheets
            
        except Exception as e:
            logger.error(f"Error listing worksheets: {str(e)}")
            raise


def create_sheets_client(spreadsheet_id: str = SPREADSHEET_ID) -> SheetsClient:
    """
    Create a Google Sheets client instance.
    
    Args:
        spreadsheet_id: Google Sheets spreadsheet ID
        
    Returns:
        Initialized SheetsClient instance
    """
    return SheetsClient(spreadsheet_id)


def main():
    """
    Main function for testing the Sheets client.
    """
    try:
        # Create client
        client = create_sheets_client()
        
        # Test basic functionality
        print("Testing Google Sheets client...")
        
        # Get spreadsheet info
        info = client.get_spreadsheet_info()
        print(f"Spreadsheet: {info.get('properties', {}).get('title', 'Unknown')}")
        
        # List worksheets
        worksheets = client.list_worksheets()
        print(f"Worksheets: {worksheets}")
        
        # Test reading from RawData!A1
        try:
            values = client.get_values('RawData!A1')
            print(f"RawData!A1 value: {values}")
        except Exception as e:
            print(f"Could not read RawData!A1: {str(e)}")
        
        print("Google Sheets client test completed successfully!")
        
    except Exception as e:
        print(f"Error testing Sheets client: {str(e)}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
