#!/usr/bin/env python3
"""
Example usage of the Google Sheets API client with Application Default Credentials.

This example demonstrates how to use the sheets.py module to:
- Authenticate using service account credentials
- Read data from Google Sheets
- Write data to Google Sheets
- List worksheets
- Handle errors gracefully

Prerequisites:
1. Set GOOGLE_APPLICATION_CREDENTIALS environment variable to point to your service account JSON file
2. Ensure the service account has access to the target spreadsheet
3. Install required dependencies: google-api-python-client, google-auth

PepWorkday Configuration:
- Spreadsheet ID: 1e5lulkbbwk6F9Xu97K38f40PUGVdp_f7W9qh31UglcU
- Service Account: pepmove@pepworkday.iam.gserviceaccount.com
"""

import os
import sys
from datetime import datetime

# Add the scripts directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

try:
    from sheets import create_sheets_client, SPREADSHEET_ID
except ImportError as e:
    print(f"Error importing sheets module: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


def example_read_data():
    """Example: Read data from Google Sheets."""
    print("\n=== Reading Data from Google Sheets ===")
    
    try:
        # Create client
        client = create_sheets_client()
        
        # Read header row from RawData worksheet
        print("Reading header row from RawData!A1:Z1...")
        headers = client.get_values('RawData!A1:Z1')
        
        if headers:
            print(f"Found {len(headers[0])} columns:")
            for i, header in enumerate(headers[0][:10]):  # Show first 10 columns
                print(f"  {i+1}. {header}")
            if len(headers[0]) > 10:
                print(f"  ... and {len(headers[0]) - 10} more columns")
        else:
            print("No headers found")
        
        # Read first few data rows
        print("\nReading first 5 data rows from RawData!A2:J6...")
        data_rows = client.get_values('RawData!A2:J6')
        
        if data_rows:
            print(f"Found {len(data_rows)} data rows:")
            for i, row in enumerate(data_rows):
                print(f"  Row {i+2}: {row[:3]}...")  # Show first 3 columns
        else:
            print("No data rows found")
            
    except Exception as e:
        print(f"Error reading data: {str(e)}")


def example_write_data():
    """Example: Write data to Google Sheets (be careful with this!)."""
    print("\n=== Writing Data to Google Sheets ===")
    
    try:
        # Create client
        client = create_sheets_client()
        
        # Prepare sample data with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sample_data = [
            ['Example Data', 'Test Value', timestamp],
            ['Sample Row 1', 'Value 1', 'Data 1'],
            ['Sample Row 2', 'Value 2', 'Data 2']
        ]
        
        # Write to a test range (be careful not to overwrite important data!)
        test_range = 'RawData!AA1:AC3'  # Using columns AA-AC to avoid conflicts
        
        print(f"Writing sample data to {test_range}...")
        print("Sample data:")
        for i, row in enumerate(sample_data):
            print(f"  Row {i+1}: {row}")
        
        # Uncomment the next line to actually write data (commented for safety)
        # result = client.update_values(test_range, sample_data)
        # print(f"Successfully updated {result.get('updatedCells', 0)} cells")
        
        print("(Write operation commented out for safety - uncomment to actually write)")
        
    except Exception as e:
        print(f"Error writing data: {str(e)}")


def example_append_data():
    """Example: Append data to Google Sheets."""
    print("\n=== Appending Data to Google Sheets ===")
    
    try:
        # Create client
        client = create_sheets_client()
        
        # Prepare data to append
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        append_data = [
            ['Appended Row', 'New Data', timestamp]
        ]
        
        # Append to a test range
        test_range = 'RawData!AA:AC'  # Using columns AA-AC to avoid conflicts
        
        print(f"Appending data to {test_range}...")
        print("Data to append:")
        for i, row in enumerate(append_data):
            print(f"  Row {i+1}: {row}")
        
        # Uncomment the next line to actually append data (commented for safety)
        # result = client.append_values(test_range, append_data)
        # print(f"Successfully appended {result.get('updates', {}).get('updatedCells', 0)} cells")
        
        print("(Append operation commented out for safety - uncomment to actually append)")
        
    except Exception as e:
        print(f"Error appending data: {str(e)}")


def example_list_worksheets():
    """Example: List all worksheets in the spreadsheet."""
    print("\n=== Listing Worksheets ===")
    
    try:
        # Create client
        client = create_sheets_client()
        
        # Get spreadsheet info
        info = client.get_spreadsheet_info()
        title = info.get('properties', {}).get('title', 'Unknown')
        
        print(f"Spreadsheet: {title}")
        print(f"Spreadsheet ID: {SPREADSHEET_ID}")
        
        # List worksheets
        worksheets = client.list_worksheets()
        
        print(f"\nFound {len(worksheets)} worksheets:")
        for i, worksheet in enumerate(worksheets):
            print(f"  {i+1}. {worksheet}")
            
    except Exception as e:
        print(f"Error listing worksheets: {str(e)}")


def example_error_handling():
    """Example: Demonstrate error handling."""
    print("\n=== Error Handling Examples ===")
    
    try:
        # Create client
        client = create_sheets_client()
        
        # Try to read from a non-existent range
        print("Attempting to read from non-existent worksheet...")
        try:
            values = client.get_values('NonExistentSheet!A1:B2')
            print(f"Unexpected success: {values}")
        except Exception as e:
            print(f"Expected error caught: {type(e).__name__}: {str(e)}")
        
        # Try to read from an invalid range
        print("\nAttempting to read from invalid range...")
        try:
            values = client.get_values('RawData!INVALID_RANGE')
            print(f"Unexpected success: {values}")
        except Exception as e:
            print(f"Expected error caught: {type(e).__name__}: {str(e)}")
            
    except Exception as e:
        print(f"Error in error handling example: {str(e)}")


def main():
    """Main function to run all examples."""
    print("Google Sheets API Client Examples")
    print("=" * 50)
    
    # Check if credentials are set
    credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if not credentials_path:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
        print("Please set it to the path of your service account JSON file:")
        print("  export GOOGLE_APPLICATION_CREDENTIALS=/path/to/pepmove-service-account.json")
        return 1
    
    if not os.path.exists(credentials_path):
        print(f"❌ Credentials file not found: {credentials_path}")
        return 1
    
    print(f"✅ Using credentials: {credentials_path}")
    print(f"✅ Target spreadsheet: {SPREADSHEET_ID}")
    
    # Run examples
    try:
        example_list_worksheets()
        example_read_data()
        example_write_data()
        example_append_data()
        example_error_handling()
        
        print("\n" + "=" * 50)
        print("✅ All examples completed successfully!")
        print("\nNote: Write and append operations were commented out for safety.")
        print("Uncomment them in the code if you want to actually modify the spreadsheet.")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Example execution failed: {str(e)}")
        return 1


if __name__ == '__main__':
    exit(main())
