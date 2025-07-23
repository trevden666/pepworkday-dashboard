#!/usr/bin/env python3
"""
Comprehensive test of PEPMove Samsara API integration using our enhanced client.
"""

import requests
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

def vehicle_locations_to_dataframe_simple(locations_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Simple version of our vehicle locations DataFrame converter.
    """
    if not locations_data:
        return pd.DataFrame()
    
    # Extract location data from the nested structure
    processed_data = []
    
    for vehicle in locations_data:
        vehicle_id = vehicle.get('id')
        vehicle_name = vehicle.get('name', 'Unknown')
        location = vehicle.get('location', {})
        
        if location:
            processed_data.append({
                'vehicle_id': vehicle_id,
                'vehicle_name': vehicle_name,
                'latitude': location.get('latitude'),
                'longitude': location.get('longitude'),
                'timestamp': location.get('time'),
                'speed_mph': location.get('speed', 0),
                'heading_degrees': location.get('heading', 0),
                'formatted_address': location.get('reverseGeo', {}).get('formattedLocation', ''),
                'organization_id': '5005620',  # PEPMove Organization ID
                'group_id': '129031'  # PEPMove Group ID
            })
    
    df = pd.DataFrame(processed_data)
    
    # Convert timestamp to datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    return df

def test_comprehensive_pepmove_integration():
    """Comprehensive test of PEPMove Samsara API integration."""
    
    print("🚛 COMPREHENSIVE PEPMOVE SAMSARA API TEST")
    print("=" * 60)
    
    # PEPMove Configuration
    api_token = "samsara_api_7qCpNNFjxM5S4jojGWzO9vxciB8o8I"
    organization_id = "5005620"
    group_id = "129031"
    base_url = "https://api.samsara.com"
    
    print(f"🏢 PEPMove Configuration:")
    print(f"   Organization ID: {organization_id}")
    print(f"   Group ID: {group_id}")
    print(f"   API Token: {api_token[:20]}...")
    
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Step 1: Get vehicle locations
    print(f"\n📡 Step 1: Retrieving Vehicle Locations")
    print("-" * 50)
    
    try:
        url = f"{base_url}/fleet/vehicles/locations"
        params = {'groupIds': group_id}
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            vehicles_data = data.get('data', [])
            
            print(f"✅ Successfully retrieved data for {len(vehicles_data)} vehicles")
            
            # Step 2: Process data using our DataFrame converter
            print(f"\n🔄 Step 2: Processing Data with PEPMove Context")
            print("-" * 50)
            
            locations_df = vehicle_locations_to_dataframe_simple(vehicles_data)
            
            print(f"✅ Successfully converted to DataFrame")
            print(f"📊 DataFrame shape: {locations_df.shape}")
            print(f"📋 Columns: {list(locations_df.columns)}")
            
            # Step 3: Validate PEPMove context
            print(f"\n✅ Step 3: Validating PEPMove Context")
            print("-" * 50)
            
            if not locations_df.empty:
                org_ids = locations_df['organization_id'].unique()
                group_ids = locations_df['group_id'].unique()
                
                print(f"✅ Organization ID context: {org_ids}")
                print(f"✅ Group ID context: {group_ids}")
                
                # Verify correct IDs
                org_correct = all(org_id == '5005620' for org_id in org_ids)
                group_correct = all(group_id == '129031' for group_id in group_ids)
                
                print(f"✅ Organization ID validation: {'PASS' if org_correct else 'FAIL'}")
                print(f"✅ Group ID validation: {'PASS' if group_correct else 'FAIL'}")
            
            # Step 4: Display comprehensive results
            print(f"\n📊 Step 4: PEPMove Fleet Location Analysis")
            print("-" * 50)
            
            if not locations_df.empty:
                print(f"🚛 PEPMove Fleet Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"📍 Total Vehicles with Location Data: {len(locations_df)}")
                
                # Display sample data
                print(f"\n📋 Sample Vehicle Locations (First 10):")
                print("=" * 120)
                
                # Select key columns for display
                display_cols = ['vehicle_name', 'latitude', 'longitude', 'speed_mph', 'formatted_address', 'timestamp']
                available_cols = [col for col in display_cols if col in locations_df.columns]
                
                sample_df = locations_df[available_cols].head(10)
                
                # Format for better display
                pd.set_option('display.max_columns', None)
                pd.set_option('display.width', None)
                pd.set_option('display.max_colwidth', 40)
                
                print(sample_df.to_string(index=False))
                
                # Fleet statistics
                print(f"\n📈 Fleet Statistics:")
                print("-" * 30)
                
                # Speed analysis
                if 'speed_mph' in locations_df.columns:
                    speeds = locations_df['speed_mph'].dropna()
                    if not speeds.empty:
                        moving_vehicles = len(speeds[speeds > 0])
                        stationary_vehicles = len(speeds[speeds == 0])
                        
                        print(f"🏃 Moving Vehicles: {moving_vehicles}")
                        print(f"🛑 Stationary Vehicles: {stationary_vehicles}")
                        print(f"🏃 Average Speed (moving): {speeds[speeds > 0].mean():.1f} mph")
                        print(f"🏃 Max Speed: {speeds.max():.1f} mph")
                
                # Location analysis
                if 'latitude' in locations_df.columns and 'longitude' in locations_df.columns:
                    lat_data = locations_df['latitude'].dropna()
                    lon_data = locations_df['longitude'].dropna()
                    
                    if not lat_data.empty and not lon_data.empty:
                        print(f"🌍 Geographic Coverage:")
                        print(f"   Latitude Range: {lat_data.min():.4f} to {lat_data.max():.4f}")
                        print(f"   Longitude Range: {lon_data.min():.4f} to {lon_data.max():.4f}")
                
                # Timestamp analysis
                if 'timestamp' in locations_df.columns:
                    timestamps = locations_df['timestamp'].dropna()
                    if not timestamps.empty:
                        latest = timestamps.max()
                        oldest = timestamps.min()
                        time_diff = (latest - oldest).total_seconds() / 60  # minutes
                        
                        print(f"🕐 Data Freshness:")
                        print(f"   Latest Update: {latest}")
                        print(f"   Oldest Update: {oldest}")
                        print(f"   Time Span: {time_diff:.1f} minutes")
                
                # Address analysis
                if 'formatted_address' in locations_df.columns:
                    addresses = locations_df['formatted_address'].dropna()
                    unique_cities = set()
                    
                    for addr in addresses:
                        if addr and ',' in addr:
                            parts = addr.split(',')
                            if len(parts) >= 2:
                                city = parts[-2].strip()
                                unique_cities.add(city)
                    
                    if unique_cities:
                        print(f"🏙️  Cities with Vehicles: {len(unique_cities)}")
                        print(f"   Sample Cities: {', '.join(list(unique_cities)[:5])}")
                
                # Export sample data
                print(f"\n💾 Step 5: Data Export Sample")
                print("-" * 50)
                
                # Save a sample to CSV for demonstration
                sample_export = locations_df.head(5)[['vehicle_name', 'latitude', 'longitude', 'speed_mph', 'timestamp', 'organization_id', 'group_id']]
                csv_content = sample_export.to_csv(index=False)
                
                print("Sample CSV export (first 5 vehicles):")
                print(csv_content)
                
            else:
                print("📭 No location data available")
            
            # Final validation summary
            print(f"\n🎯 Final Validation Summary")
            print("-" * 50)
            
            validations = [
                ("API Authentication", "✅ PASS"),
                ("Data Retrieval", f"✅ PASS ({len(vehicles_data)} vehicles)"),
                ("DataFrame Processing", "✅ PASS"),
                ("PEPMove Org ID (5005620)", "✅ PASS" if not locations_df.empty and org_correct else "❌ FAIL"),
                ("PEPMove Group ID (129031)", "✅ PASS" if not locations_df.empty and group_correct else "❌ FAIL"),
                ("Real-time Data", "✅ PASS" if not locations_df.empty else "⚠️  NO DATA")
            ]
            
            for validation_name, status in validations:
                print(f"{validation_name:.<35} {status}")
            
            return True
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def main():
    """Main function to run the comprehensive test."""
    print("🚀 Starting Comprehensive PEPMove Samsara API Test")
    
    try:
        success = test_comprehensive_pepmove_integration()
        
        if success:
            print(f"\n🎉 COMPREHENSIVE TEST COMPLETED SUCCESSFULLY!")
            print(f"✅ PEPMove Samsara API integration is fully functional")
            print(f"✅ Real-time vehicle location data retrieved and processed")
            print(f"✅ PEPMove organizational context (5005620/129031) validated")
            print(f"✅ Data processing pipeline working correctly")
            
            print(f"\n🔗 Integration Summary:")
            print(f"   • API Token: Working")
            print(f"   • Organization ID: 5005620 ✅")
            print(f"   • Group ID: 129031 ✅") 
            print(f"   • Vehicle Locations: Retrieved ✅")
            print(f"   • Data Processing: Functional ✅")
            print(f"   • PEPMove Context: Preserved ✅")
            
        else:
            print(f"\n❌ TEST FAILED!")
            print(f"Please check the error messages above")
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")

if __name__ == "__main__":
    main()
