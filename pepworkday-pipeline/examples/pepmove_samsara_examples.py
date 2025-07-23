"""
PEPMove Samsara API Usage Examples

This module demonstrates how to use the enhanced Samsara API client
with PEPMove's specific configuration and endpoints.

Organization ID: 5005620
Group ID: 129031
API Token: [Set via SAMSARA_API_TOKEN environment variable]
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd

from ..utils.samsara_api import (
    create_samsara_client,
    SamsaraAPIClient,
    trips_to_dataframe,
    vehicle_locations_to_dataframe,
    addresses_to_dataframe,
    routes_to_dataframe
)
from ..config.settings import settings


def example_basic_fleet_data():
    """Example: Get basic PEPMove fleet data."""
    print("=== PEPMove Basic Fleet Data Example ===")
    
    # Create PEPMove-configured client
    client = create_samsara_client()
    
    try:
        # Get vehicles in PEPMove group
        vehicles = client.get_vehicles()
        print(f"Found {len(vehicles)} vehicles in PEPMove fleet (Group {settings.samsara.group_id})")
        
        # Get current vehicle locations
        locations = client.get_vehicle_locations()
        locations_df = vehicle_locations_to_dataframe(locations)
        print(f"Current locations for {len(locations_df)} vehicles")
        print(locations_df[['vehicle_id', 'latitude', 'longitude', 'timestamp']].head())
        
        # Get drivers
        drivers = client.get_drivers()
        print(f"Found {len(drivers)} drivers in PEPMove organization")
        
        return {
            'vehicles': vehicles,
            'locations': locations_df,
            'drivers': drivers
        }
        
    except Exception as e:
        print(f"Error getting basic fleet data: {str(e)}")
        return None


def example_trip_analysis():
    """Example: Analyze PEPMove trips for the last 7 days."""
    print("\n=== PEPMove Trip Analysis Example ===")
    
    client = create_samsara_client()
    
    try:
        # Get trips for the last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        print(f"Analyzing trips from {start_date.date()} to {end_date.date()}")
        
        trips = client.get_fleet_trips(start_date, end_date)
        trips_df = trips_to_dataframe(trips)
        
        if not trips_df.empty:
            # Basic trip statistics
            total_trips = len(trips_df)
            total_miles = trips_df['total_miles'].sum()
            avg_trip_miles = trips_df['total_miles'].mean()
            total_idle_time = trips_df['idle_time'].sum()
            
            print(f"Trip Analysis Results:")
            print(f"  Total Trips: {total_trips}")
            print(f"  Total Miles: {total_miles:.1f}")
            print(f"  Average Trip Miles: {avg_trip_miles:.1f}")
            print(f"  Total Idle Time: {total_idle_time:.1f} minutes")
            
            # Top drivers by miles
            if 'driver_id' in trips_df.columns:
                driver_miles = trips_df.groupby('driver_id')['total_miles'].sum().sort_values(ascending=False)
                print(f"\nTop 5 Drivers by Miles:")
                for driver_id, miles in driver_miles.head().items():
                    print(f"  {driver_id}: {miles:.1f} miles")
            
            return trips_df
        else:
            print("No trips found for the specified date range")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Error analyzing trips: {str(e)}")
        return None


def example_real_time_monitoring():
    """Example: Real-time monitoring of PEPMove fleet."""
    print("\n=== PEPMove Real-Time Monitoring Example ===")
    
    client = create_samsara_client()
    
    try:
        # Get real-time vehicle stats
        stats = client.get_real_time_vehicle_stats(
            stat_types=['engineStates', 'fuelPercentages', 'locations']
        )
        
        print(f"Real-time stats for {len(stats)} vehicles:")
        
        # Process stats
        active_vehicles = 0
        idle_vehicles = 0
        
        for vehicle_stat in stats:
            vehicle_id = vehicle_stat.get('vehicleId', 'Unknown')
            engine_state = vehicle_stat.get('engineState', 'Unknown')
            fuel_percent = vehicle_stat.get('fuelPercent', 'Unknown')
            
            if engine_state == 'Running':
                active_vehicles += 1
            elif engine_state == 'Off':
                idle_vehicles += 1
            
            print(f"  Vehicle {vehicle_id}: Engine {engine_state}, Fuel {fuel_percent}%")
        
        print(f"\nFleet Summary:")
        print(f"  Active Vehicles: {active_vehicles}")
        print(f"  Idle Vehicles: {idle_vehicles}")
        
        return stats
        
    except Exception as e:
        print(f"Error getting real-time stats: {str(e)}")
        return None


def example_address_management():
    """Example: Manage addresses for PEPMove operations."""
    print("\n=== PEPMove Address Management Example ===")
    
    client = create_samsara_client()
    
    try:
        # Get existing addresses
        addresses = client.get_addresses()
        addresses_df = addresses_to_dataframe(addresses)
        
        print(f"Found {len(addresses_df)} existing addresses in PEPMove organization")
        
        if not addresses_df.empty:
            print("Existing addresses:")
            print(addresses_df[['address_name', 'formatted_address', 'latitude', 'longitude']].head())
        
        # Example: Create a new address (commented out to avoid actual creation)
        """
        new_address = client.create_address(
            name="PEPMove Depot - Example",
            formatted_address="123 Main St, Anytown, ST 12345",
            latitude=40.7128,
            longitude=-74.0060,
            notes="Example depot location for PEPMove operations",
            tags=["depot", "pepmove", "example"]
        )
        print(f"Created new address: {new_address}")
        """
        
        return addresses_df
        
    except Exception as e:
        print(f"Error managing addresses: {str(e)}")
        return None


def example_route_management():
    """Example: Manage routes for PEPMove operations."""
    print("\n=== PEPMove Route Management Example ===")
    
    client = create_samsara_client()
    
    try:
        # Get existing routes
        routes = client.get_routes()
        routes_df = routes_to_dataframe(routes)
        
        print(f"Found {len(routes_df)} routes in PEPMove organization")
        
        if not routes_df.empty:
            print("Recent routes:")
            print(routes_df[['route_name', 'driver_id', 'vehicle_id', 'start_time', 'waypoint_count']].head())
        
        # Example: Create a new route (commented out to avoid actual creation)
        """
        waypoints = [
            {
                "address": "123 Start St, City, ST 12345",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "name": "Pickup Location"
            },
            {
                "address": "456 End Ave, City, ST 12345",
                "latitude": 40.7589,
                "longitude": -73.9851,
                "name": "Delivery Location"
            }
        ]
        
        new_route = client.create_route(
            name="PEPMove Delivery Route - Example",
            driver_id="driver_123",
            vehicle_id="vehicle_456",
            waypoints=waypoints,
            start_time=datetime.now() + timedelta(hours=1)
        )
        print(f"Created new route: {new_route}")
        """
        
        return routes_df
        
    except Exception as e:
        print(f"Error managing routes: {str(e)}")
        return None


def example_comprehensive_fleet_summary():
    """Example: Generate comprehensive PEPMove fleet summary."""
    print("\n=== PEPMove Comprehensive Fleet Summary ===")
    
    client = create_samsara_client()
    
    try:
        # Use the built-in fleet summary method
        summary = client.get_pepmove_fleet_summary()
        
        print(f"PEPMove Fleet Summary (Org: {summary['organization_id']}, Group: {summary['group_id']}):")
        print(f"  Total Vehicles: {summary['total_vehicles']}")
        print(f"  Vehicles with Location Data: {summary['vehicles_with_location']}")
        print(f"  Vehicles with Stats: {summary['vehicles_with_stats']}")
        print(f"  Summary Generated: {summary['timestamp']}")
        
        # Additional analysis
        if summary['locations']:
            locations_df = vehicle_locations_to_dataframe(summary['locations'])
            if not locations_df.empty:
                print(f"\nLocation Summary:")
                print(f"  Average Speed: {locations_df['speed_mph'].mean():.1f} mph")
                print(f"  Speed Range: {locations_df['speed_mph'].min():.1f} - {locations_df['speed_mph'].max():.1f} mph")
        
        return summary
        
    except Exception as e:
        print(f"Error generating fleet summary: {str(e)}")
        return None


def example_historical_location_tracking():
    """Example: Track historical locations for PEPMove vehicles."""
    print("\n=== PEPMove Historical Location Tracking ===")
    
    client = create_samsara_client()
    
    try:
        # Get location history for the last 24 hours
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        print(f"Getting location history from {start_time} to {end_time}")
        
        # Get specific vehicles (you can specify vehicle IDs here)
        location_history = client.get_vehicle_locations_history(
            start_time=start_time,
            end_time=end_time
            # vehicle_ids=['vehicle_123', 'vehicle_456']  # Optional filter
        )
        
        locations_df = vehicle_locations_to_dataframe(location_history)
        
        if not locations_df.empty:
            print(f"Found {len(locations_df)} location records")
            
            # Analyze movement patterns
            vehicle_counts = locations_df['vehicle_id'].value_counts()
            print(f"\nLocation records per vehicle:")
            for vehicle_id, count in vehicle_counts.head().items():
                print(f"  {vehicle_id}: {count} records")
            
            # Time-based analysis
            if 'timestamp' in locations_df.columns:
                locations_df['hour'] = locations_df['timestamp'].dt.hour
                hourly_activity = locations_df['hour'].value_counts().sort_index()
                print(f"\nActivity by hour:")
                for hour, count in hourly_activity.items():
                    print(f"  {hour:02d}:00: {count} location updates")
        
        return locations_df
        
    except Exception as e:
        print(f"Error tracking historical locations: {str(e)}")
        return None


def run_all_examples():
    """Run all PEPMove Samsara API examples."""
    print("Running PEPMove Samsara API Examples")
    print("=" * 50)
    
    examples = [
        example_basic_fleet_data,
        example_trip_analysis,
        example_real_time_monitoring,
        example_address_management,
        example_route_management,
        example_comprehensive_fleet_summary,
        example_historical_location_tracking
    ]
    
    results = {}
    
    for example_func in examples:
        try:
            result = example_func()
            results[example_func.__name__] = result
        except Exception as e:
            print(f"Error running {example_func.__name__}: {str(e)}")
            results[example_func.__name__] = None
        
        print("\n" + "-" * 50)
    
    return results


if __name__ == "__main__":
    # Run all examples
    results = run_all_examples()
    
    print("\nExample execution completed!")
    print(f"Successfully ran {sum(1 for r in results.values() if r is not None)} out of {len(results)} examples")
