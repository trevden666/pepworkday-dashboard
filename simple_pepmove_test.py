#!/usr/bin/env python3
"""
Simple test script for PEPMove Samsara API integration.
"""

import requests
import json
from datetime import datetime

def test_pepmove_samsara_api():
    """Test PEPMove Samsara API with direct HTTP requests."""
    
    print("🚛 Testing PEPMove Samsara API Integration")
    print("=" * 50)
    
    # PEPMove Configuration
    api_token = os.getenv("SAMSARA_API_TOKEN", "your_api_token_here")
    organization_id = "5005620"
    group_id = "129031"
    base_url = "https://api.samsara.com"
    
    print(f"Organization ID: {organization_id}")
    print(f"Group ID: {group_id}")
    print(f"API Token: {api_token[:20]}...")
    
    # Set up headers
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Test 1: Get vehicle locations
    print(f"\n📡 Test 1: Getting Vehicle Locations")
    print("-" * 30)
    
    try:
        url = f"{base_url}/fleet/vehicles/locations"
        params = {
            'groupIds': group_id
        }
        
        print(f"Making request to: {url}")
        print(f"Parameters: {params}")
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Retrieved data:")
            print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            if 'data' in data:
                vehicles = data['data']
                print(f"Number of vehicles: {len(vehicles)}")
                
                if vehicles:
                    print(f"\nSample vehicle data:")
                    sample = vehicles[0]
                    for key, value in sample.items():
                        print(f"  {key}: {value}")
                else:
                    print("No vehicle data returned")
            else:
                print(f"Full response: {json.dumps(data, indent=2)}")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Test 2: Get vehicles list
    print(f"\n📡 Test 2: Getting Vehicles List")
    print("-" * 30)
    
    try:
        url = f"{base_url}/fleet/vehicles"
        params = {
            'groupIds': group_id
        }
        
        print(f"Making request to: {url}")
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            
            if 'data' in data:
                vehicles = data['data']
                print(f"Number of vehicles in fleet: {len(vehicles)}")
                
                if vehicles:
                    print(f"\nVehicle IDs:")
                    for i, vehicle in enumerate(vehicles[:5]):  # Show first 5
                        vehicle_id = vehicle.get('id', 'Unknown')
                        vehicle_name = vehicle.get('name', 'Unnamed')
                        print(f"  {i+1}. {vehicle_id} - {vehicle_name}")
                    
                    if len(vehicles) > 5:
                        print(f"  ... and {len(vehicles) - 5} more vehicles")
            else:
                print(f"Unexpected response format: {list(data.keys())}")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Test 3: Test authentication
    print(f"\n📡 Test 3: Testing Authentication")
    print("-" * 30)
    
    try:
        # Try a simple endpoint that should work with valid auth
        url = f"{base_url}/fleet/drivers"
        params = {
            'groupIds': group_id,
            'limit': 1
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Authentication successful!")
            data = response.json()
            if 'data' in data:
                drivers = data['data']
                print(f"Found {len(drivers)} drivers in the response")
        elif response.status_code == 401:
            print(f"❌ Authentication failed - Invalid API token")
        elif response.status_code == 403:
            print(f"❌ Authorization failed - Insufficient permissions")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print(f"\n🎉 PEPMove Samsara API Test Complete!")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    test_pepmove_samsara_api()
