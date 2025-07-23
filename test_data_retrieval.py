#!/usr/bin/env python3
"""
Comprehensive data retrieval test for Google Sheets API client.
This script tests the new data added to the PepWorkday spreadsheet.
"""

import os
import sys
from datetime import datetime

# Add the scripts directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

try:
    from sheets import create_sheets_client, SPREADSHEET_ID
except ImportError as e:
    print(f"❌ Error importing sheets module: {e}")
    sys.exit(1)


def test_authentication():
    """Test basic authentication and connection."""
    print("🔐 AUTHENTICATION TEST")
    print("=" * 50)
    
    try:
        # Check environment variable
        creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path:
            print("❌ GOOGLE_APPLICATION_CREDENTIALS not set")
            return False
        
        print(f"✅ Credentials path: {creds_path}")
        print(f"✅ Credentials file exists: {os.path.exists(creds_path)}")
        print(f"✅ Target spreadsheet: {SPREADSHEET_ID}")
        
        # Create client
        client = create_sheets_client()
        print("✅ Google Sheets client created successfully")
        
        # Test basic read
        values = client.get_values('RawData!A1')
        print(f"✅ Basic read test successful: {type(values)} with {len(values)} items")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")
        return False


def test_header_row():
    """Test reading the header row from RawData!A1:Z1."""
    print("\n📋 HEADER ROW TEST")
    print("=" * 50)
    
    try:
        client = create_sheets_client()
        
        # Read header row
        headers = client.get_values('RawData!A1:Z1')
        
        if not headers:
            print("❌ No header data found")
            return False
        
        header_row = headers[0] if headers else []
        print(f"✅ Found {len(header_row)} columns in header row")
        
        # Display headers with numbering
        print("\n📊 Column Structure:")
        for i, header in enumerate(header_row):
            if header.strip():  # Only show non-empty headers
                print(f"  {i+1:2d}. {header}")
        
        # Show empty columns
        empty_cols = [i+1 for i, h in enumerate(header_row) if not h.strip()]
        if empty_cols:
            print(f"\n⚠️  Empty columns: {empty_cols}")
        
        return True
        
    except Exception as e:
        print(f"❌ Header row test failed: {str(e)}")
        return False


def test_data_rows():
    """Test reading the first 10 data rows from RawData!A2:Z11."""
    print("\n📊 DATA ROWS TEST")
    print("=" * 50)
    
    try:
        client = create_sheets_client()
        
        # Read data rows
        data_rows = client.get_values('RawData!A2:Z11')
        
        if not data_rows:
            print("❌ No data rows found")
            return False
        
        print(f"✅ Found {len(data_rows)} data rows")
        
        # Display data summary
        print(f"\n📈 Data Summary:")
        print(f"  Total rows retrieved: {len(data_rows)}")
        
        # Analyze each row
        for i, row in enumerate(data_rows):
            row_num = i + 2  # Actual row number in spreadsheet
            non_empty_cells = len([cell for cell in row if str(cell).strip()])
            print(f"  Row {row_num:2d}: {non_empty_cells:2d} non-empty cells, {len(row):2d} total cells")
        
        # Show sample data from first few rows
        print(f"\n📋 Sample Data (First 3 Rows, First 6 Columns):")
        for i, row in enumerate(data_rows[:3]):
            row_num = i + 2
            sample_data = row[:6] if len(row) >= 6 else row
            # Truncate long values for display
            display_data = [str(cell)[:20] + "..." if len(str(cell)) > 20 else str(cell) for cell in sample_data]
            print(f"  Row {row_num}: {display_data}")
        
        # Check for completely empty rows
        empty_rows = [i+2 for i, row in enumerate(data_rows) if not any(str(cell).strip() for cell in row)]
        if empty_rows:
            print(f"\n⚠️  Empty rows found: {empty_rows}")
        else:
            print(f"\n✅ All rows contain data")
        
        return True
        
    except Exception as e:
        print(f"❌ Data rows test failed: {str(e)}")
        return False


def test_specific_data_analysis():
    """Perform detailed analysis of the new data."""
    print("\n🔍 DETAILED DATA ANALYSIS")
    print("=" * 50)
    
    try:
        client = create_sheets_client()
        
        # Get headers first
        headers = client.get_values('RawData!A1:Z1')
        header_row = headers[0] if headers else []
        
        # Get data
        data_rows = client.get_values('RawData!A2:Z11')
        
        if not data_rows:
            print("❌ No data available for analysis")
            return False
        
        print(f"✅ Analyzing {len(data_rows)} rows with {len(header_row)} columns")
        
        # Create column analysis
        column_analysis = {}
        for col_idx, header in enumerate(header_row):
            if not header.strip():
                continue
                
            values = []
            for row in data_rows:
                if col_idx < len(row):
                    cell_value = str(row[col_idx]).strip()
                    if cell_value:
                        values.append(cell_value)
            
            column_analysis[header] = {
                'non_empty_count': len(values),
                'sample_values': values[:3],  # First 3 values
                'unique_count': len(set(values)) if values else 0
            }
        
        # Display analysis
        print(f"\n📊 Column Analysis:")
        for header, analysis in column_analysis.items():
            if analysis['non_empty_count'] > 0:
                print(f"  {header}:")
                print(f"    Non-empty cells: {analysis['non_empty_count']}")
                print(f"    Unique values: {analysis['unique_count']}")
                print(f"    Sample values: {analysis['sample_values']}")
                print()
        
        # Look for key columns that might indicate new data
        key_columns = ['driver_name', 'date', 'route', 'miles', 'stops', '_kp_job_id']
        found_key_columns = []
        
        for key_col in key_columns:
            for header in header_row:
                if key_col.lower() in header.lower():
                    found_key_columns.append(header)
                    break
        
        if found_key_columns:
            print(f"✅ Found key columns: {found_key_columns}")
        else:
            print(f"⚠️  No standard key columns found")
        
        return True
        
    except Exception as e:
        print(f"❌ Data analysis failed: {str(e)}")
        return False


def test_worksheet_listing():
    """Test listing all worksheets in the spreadsheet."""
    print("\n📑 WORKSHEET LISTING TEST")
    print("=" * 50)
    
    try:
        client = create_sheets_client()
        
        # Get spreadsheet info
        info = client.get_spreadsheet_info()
        title = info.get('properties', {}).get('title', 'Unknown')
        
        print(f"✅ Spreadsheet: {title}")
        print(f"✅ Spreadsheet ID: {SPREADSHEET_ID}")
        
        # List worksheets
        worksheets = client.list_worksheets()
        
        print(f"✅ Found {len(worksheets)} worksheets:")
        for i, worksheet in enumerate(worksheets):
            print(f"  {i+1}. {worksheet}")
        
        # Test reading from each worksheet (just A1 cell)
        print(f"\n🔍 Testing access to each worksheet:")
        for worksheet in worksheets:
            try:
                values = client.get_values(f'{worksheet}!A1')
                status = "✅ Accessible"
                if values and values[0] and values[0][0]:
                    sample = str(values[0][0])[:30]
                    status += f" (A1: '{sample}')"
                else:
                    status += " (A1: empty)"
            except Exception as e:
                status = f"❌ Error: {str(e)[:50]}"
            
            print(f"  {worksheet}: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Worksheet listing failed: {str(e)}")
        return False


def main():
    """Run comprehensive data retrieval tests."""
    print("🚀 COMPREHENSIVE GOOGLE SHEETS DATA RETRIEVAL TEST")
    print("=" * 70)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target Spreadsheet: {SPREADSHEET_ID}")
    print("=" * 70)
    
    # Run all tests
    tests = [
        ("Authentication", test_authentication),
        ("Header Row", test_header_row),
        ("Data Rows", test_data_rows),
        ("Data Analysis", test_specific_data_analysis),
        ("Worksheet Listing", test_worksheet_listing)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running {test_name} Test...")
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results[test_name] = False
    
    # Summary
    print(f"\n🎯 TEST SUMMARY")
    print("=" * 50)
    
    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
    
    print("-" * 50)
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {passed_tests/total_tests:.1%}")
    
    if passed_tests == total_tests:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ Google Sheets API client is fully functional")
        print(f"✅ New data is accessible and readable")
        print(f"✅ Authentication and permissions are working correctly")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} TESTS FAILED")
        print(f"❌ Some functionality needs attention")
        return 1


if __name__ == '__main__':
    exit(main())
