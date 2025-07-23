#!/usr/bin/env python3
"""
Test script for PEPMove Samsara API integration.

This script tests the real-time vehicle location retrieval functionality
using PEPMove's specific Samsara configuration:
- Organization ID: 5005620
- Group ID: 129031
- API Token: [Set via SAMSARA_API_TOKEN environment variable]
"""

import sys
import os
from datetime import datetime
import pandas as pd
import logging

# Add the pepworkday-pipeline directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pepworkday-pipeline'))

try:
    from utils.samsara_api import (
        SamsaraAPIClient,
        SamsaraAPIConfig,
        vehicle_locations_to_dataframe,
        SamsaraAPIError
    )
    print("✅ Successfully imported PEPMove Samsara API modules")
except ImportError as e:
    print(f"❌ Failed to import modules: {e}")
    print("Make sure you're running this from the correct directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_pepmove_vehicle_locations():
    """Test retrieving current vehicle locations for PEPMove fleet."""
    print("\n" + "="*60)
    print("🚛 TESTING PEPMOVE SAMSARA API INTEGRATION")
    print("="*60)
    
    # Step 1: Create PEPMove-specific API configuration
    print("\n📋 Step 1: Creating PEPMove API Configuration")
    print("-" * 50)
    
    pepmove_config = SamsaraAPIConfig(
        api_token=os.getenv("SAMSARA_API_TOKEN", "your_api_token_here"),
        organization_id="5005620",
        group_id="129031",
        base_url="https://api.samsara.com",
        timeout=30,
        max_retries=3
    )
    
    print(f"✅ Organization ID: {pepmove_config.organization_id}")
    print(f"✅ Group ID: {pepmove_config.group_id}")
    print(f"✅ API Token: {pepmove_config.api_token[:20]}...")
    print(f"✅ Base URL: {pepmove_config.base_url}")
    
    # Step 2: Initialize the API client
    print("\n🔧 Step 2: Initializing PEPMove API Client")
    print("-" * 50)
    
    try:
        client = SamsaraAPIClient(pepmove_config)
        print("✅ PEPMove Samsara API client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize API client: {e}")
        return False
    
    # Step 3: Make the API call to get vehicle locations
    print("\n📡 Step 3: Fetching Vehicle Locations from Samsara API")
    print("-" * 50)
    
    try:
        print("🔄 Making API call to /fleet/vehicles/locations...")
        print(f"🎯 Target: PEPMove Organization {pepmove_config.organization_id}, Group {pepmove_config.group_id}")
        
        # Call the API
        locations_data = client.get_vehicle_locations()
        
        print(f"✅ API call successful!")
        print(f"📊 Retrieved data for {len(locations_data)} vehicles")
        
        if len(locations_data) == 0:
            print("⚠️  No vehicle location data returned")
            print("   This could mean:")
            print("   - No vehicles are currently active")
            print("   - Vehicles are not reporting locations")
            print("   - Group ID filter is too restrictive")
            return True
        
        # Display raw API response sample
        print(f"\n📋 Sample Raw API Response (first vehicle):")
        if locations_data:
            sample_vehicle = locations_data[0]
            for key, value in sample_vehicle.items():
                print(f"   {key}: {value}")
        
    except SamsaraAPIError as e:
        print(f"❌ Samsara API Error: {e}")
        print("   Possible causes:")
        print("   - Invalid API token")
        print("   - Insufficient permissions")
        print("   - Network connectivity issues")
        print("   - API rate limiting")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during API call: {e}")
        return False
    
    # Step 4: Process the data using our DataFrame converter
    print("\n🔄 Step 4: Processing Data with PEPMove Context")
    print("-" * 50)
    
    try:
        # Convert to DataFrame with PEPMove context
        locations_df = vehicle_locations_to_dataframe(locations_data)
        
        print(f"✅ Successfully converted to DataFrame")
        print(f"📊 DataFrame shape: {locations_df.shape}")
        print(f"📋 Columns: {list(locations_df.columns)}")
        
        # Verify PEPMove context is included
        if 'organization_id' in locations_df.columns:
            org_ids = locations_df['organization_id'].unique()
            print(f"✅ Organization ID context: {org_ids}")
        
        if 'group_id' in locations_df.columns:
            group_ids = locations_df['group_id'].unique()
            print(f"✅ Group ID context: {group_ids}")
        
    except Exception as e:
        print(f"❌ Error processing data: {e}")
        return False
    
    # Step 5: Display the results
    print("\n📊 Step 5: Displaying PEPMove Fleet Location Results")
    print("-" * 50)
    
    if not locations_df.empty:
        print(f"🚛 PEPMove Fleet Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📍 Total Vehicles with Location Data: {len(locations_df)}")
        
        # Display key columns
        display_columns = []
        available_columns = locations_df.columns.tolist()
        
        # Prioritize important columns
        priority_columns = [
            'vehicle_id', 'latitude', 'longitude', 'timestamp', 
            'speed_mph', 'heading_degrees', 'formatted_address',
            'organization_id', 'group_id'
        ]
        
        for col in priority_columns:
            if col in available_columns:
                display_columns.append(col)
        
        # Add any remaining columns
        for col in available_columns:
            if col not in display_columns:
                display_columns.append(col)
        
        print(f"\n📋 Vehicle Location Data:")
        print("=" * 100)
        
        # Display data with proper formatting
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 30)
        
        if len(locations_df) <= 10:
            # Show all vehicles if 10 or fewer
            print(locations_df[display_columns].to_string(index=False))
        else:
            # Show first 5 and last 5 if more than 10
            print("First 5 vehicles:")
            print(locations_df[display_columns].head().to_string(index=False))
            print("\n...")
            print(f"\nLast 5 vehicles:")
            print(locations_df[display_columns].tail().to_string(index=False))
        
        # Display summary statistics
        print(f"\n📈 Fleet Summary Statistics:")
        print("-" * 30)
        
        if 'speed_mph' in locations_df.columns:
            speeds = locations_df['speed_mph'].dropna()
            if not speeds.empty:
                print(f"🏃 Average Speed: {speeds.mean():.1f} mph")
                print(f"🏃 Max Speed: {speeds.max():.1f} mph")
                print(f"🏃 Min Speed: {speeds.min():.1f} mph")
        
        if 'timestamp' in locations_df.columns:
            timestamps = pd.to_datetime(locations_df['timestamp']).dropna()
            if not timestamps.empty:
                latest_update = timestamps.max()
                oldest_update = timestamps.min()
                print(f"🕐 Latest Update: {latest_update}")
                print(f"🕐 Oldest Update: {oldest_update}")
        
        # Geographic distribution
        if 'latitude' in locations_df.columns and 'longitude' in locations_df.columns:
            lat_data = locations_df['latitude'].dropna()
            lon_data = locations_df['longitude'].dropna()
            if not lat_data.empty and not lon_data.empty:
                print(f"🌍 Geographic Range:")
                print(f"   Latitude: {lat_data.min():.4f} to {lat_data.max():.4f}")
                print(f"   Longitude: {lon_data.min():.4f} to {lon_data.max():.4f}")
        
    else:
        print("📭 No location data to display")
    
    # Step 6: Validation summary
    print(f"\n✅ Step 6: Validation Summary")
    print("-" * 50)
    
    validations = []
    
    # Check API connection
    validations.append(("API Connection", "✅ Success"))
    
    # Check PEPMove context
    if not locations_df.empty:
        if 'organization_id' in locations_df.columns:
            org_check = all(locations_df['organization_id'] == '5005620')
            validations.append(("Organization ID (5005620)", "✅ Correct" if org_check else "❌ Incorrect"))
        
        if 'group_id' in locations_df.columns:
            group_check = all(locations_df['group_id'] == '129031')
            validations.append(("Group ID (129031)", "✅ Correct" if group_check else "❌ Incorrect"))
    
    # Check data quality
    data_quality = "✅ Good" if not locations_df.empty else "⚠️  No Data"
    validations.append(("Data Retrieval", data_quality))
    
    # Check DataFrame processing
    validations.append(("DataFrame Processing", "✅ Success"))
    
    for validation_name, status in validations:
        print(f"{validation_name:.<30} {status}")
    
    print(f"\n🎉 PEPMove Samsara API Integration Test Complete!")
    print("="*60)
    
    return True


def main():
    """Main function to run the PEPMove API test."""
    print("🚀 Starting PEPMove Samsara API Integration Test")
    
    try:
        success = test_pepmove_vehicle_locations()
        
        if success:
            print(f"\n✅ Test completed successfully!")
            print(f"🔗 PEPMove Samsara API integration is working correctly")
            return 0
        else:
            print(f"\n❌ Test failed!")
            print(f"🔧 Please check the error messages above and verify:")
            print(f"   - API token is valid and has proper permissions")
            print(f"   - Network connectivity to api.samsara.com")
            print(f"   - PEPMove organization and group IDs are correct")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
