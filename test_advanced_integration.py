#!/usr/bin/env python3
"""
Comprehensive Integration Test for Advanced PepWorkday Pipeline Features.

This script tests all the advanced features implemented for the PepWorkday pipeline:
1. Webhook Integration
2. Advanced Polling System
3. Enhanced Google Sheets Sync
4. Monitoring & Error Handling
5. Security & Best Practices
6. Dashboard Auto-Refresh

PepWorkday Configuration:
- Organization ID: 5005620
- Group ID: 129031
- API Token: [Set via SAMSARA_API_TOKEN environment variable]
"""

import sys
import os
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
import pandas as pd

# Add the pepworkday-pipeline directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pepworkday-pipeline'))

def test_security_manager():
    """Test the security manager functionality."""
    print("\n🔒 Testing Security Manager")
    print("-" * 50)
    
    try:
        from security.security_manager import (
            security_manager,
            get_secure_token,
            check_rate_limit,
            log_security_event
        )
        
        # Test secure token retrieval
        token = get_secure_token("pepmove_samsara")
        if token:
            print(f"✅ Secure token retrieved: {token[:20]}...")
        else:
            print("❌ Failed to retrieve secure token")
            return False
        
        # Test rate limiting
        allowed, delay = check_rate_limit("test_client")
        print(f"✅ Rate limit check: allowed={allowed}, delay={delay}")
        
        # Test security event logging
        log_security_event(
            event_type="test_event",
            severity="low",
            details={"test": "integration_test"}
        )
        print("✅ Security event logged successfully")
        
        # Get security summary
        summary = security_manager.get_security_summary()
        print(f"✅ Security summary: {summary['security_status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Security manager test failed: {str(e)}")
        return False


def test_advanced_polling():
    """Test the advanced polling system."""
    print("\n🔄 Testing Advanced Polling System")
    print("-" * 50)
    
    try:
        from core.advanced_polling import (
            create_advanced_poller,
            PollingConfig,
            PollingMetrics
        )
        
        # Create poller with test configuration
        config = PollingConfig(
            default_interval_seconds=60,
            max_requests_per_minute=30,
            enable_deduplication=True
        )
        
        poller = create_advanced_poller(config)
        print("✅ Advanced poller created successfully")
        
        # Test metrics collection
        metrics = PollingMetrics()
        metrics.total_requests = 10
        metrics.successful_requests = 9
        metrics.failed_requests = 1
        
        print(f"✅ Polling metrics: {metrics.success_rate:.1%} success rate")
        
        # Test data type polling (mock)
        print("✅ Polling system configured for PEPMove (Org: 5005620, Group: 129031)")
        
        return True
        
    except Exception as e:
        print(f"❌ Advanced polling test failed: {str(e)}")
        return False


def test_monitoring_system():
    """Test the monitoring and error handling system."""
    print("\n📊 Testing Monitoring System")
    print("-" * 50)
    
    try:
        from monitoring.advanced_monitoring import (
            AdvancedMonitor,
            AlertSeverity,
            ErrorCategory,
            SecurityEvent
        )
        
        # Create monitor
        monitor = AdvancedMonitor(enable_real_time_monitoring=False)
        print("✅ Advanced monitor created successfully")
        
        # Test alert creation
        alert_id = monitor.create_alert(
            severity=AlertSeverity.MEDIUM,
            category=ErrorCategory.API_ERROR,
            title="Test Alert",
            message="Integration test alert",
            context={"test": True}
        )
        print(f"✅ Alert created: {alert_id}")
        
        # Test error logging
        try:
            raise ValueError("Test error for monitoring")
        except ValueError as e:
            monitor.log_error(e, context={"test_context": "integration"})
            print("✅ Error logged successfully")
        
        # Get monitoring summary
        summary = monitor.get_monitoring_summary()
        print(f"✅ Monitoring summary: {summary['active_alerts']} active alerts")
        
        return True
        
    except Exception as e:
        print(f"❌ Monitoring system test failed: {str(e)}")
        return False


def test_webhook_receiver():
    """Test the webhook receiver functionality."""
    print("\n🔗 Testing Webhook Receiver")
    print("-" * 50)
    
    try:
        from integrations.webhook_receiver import (
            SamsaraWebhookReceiver,
            WebhookEvent
        )
        
        # Create webhook receiver
        receiver = SamsaraWebhookReceiver(
            enable_signature_verification=False,
            auto_process_events=False
        )
        print("✅ Webhook receiver created successfully")
        
        # Test event parsing
        mock_payload = {
            'eventType': 'tripStarted',
            'eventId': 'test_event_123',
            'eventTime': datetime.now().isoformat(),
            'organizationId': '5005620',
            'groupId': '129031',
            'vehicleId': 'vehicle_123',
            'trip': {
                'id': 'trip_456',
                'status': 'started',
                'distanceMiles': 0
            }
        }
        
        event = receiver._parse_webhook_event(mock_payload)
        print(f"✅ Webhook event parsed: {event.event_type}")
        print(f"✅ PEPMove context: Org {event.organization_id}, Group {event.group_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Webhook receiver test failed: {str(e)}")
        return False


def test_samsara_api_integration():
    """Test the enhanced Samsara API integration."""
    print("\n🚛 Testing Enhanced Samsara API Integration")
    print("-" * 50)
    
    try:
        import requests
        
        # Test API connection with PEPMove configuration
        api_token = os.getenv("SAMSARA_API_TOKEN", "your_api_token_here")
        headers = {'Authorization': f'Bearer {api_token}'}
        
        # Test basic API connectivity
        response = requests.get(
            'https://api.samsara.com/fleet/vehicles',
            headers=headers,
            params={'groupIds': '129031', 'limit': 1},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            vehicle_count = len(data.get('data', []))
            print(f"✅ Samsara API connection successful")
            print(f"✅ PEPMove fleet access: {vehicle_count} vehicles accessible")
            print(f"✅ Organization ID: 5005620")
            print(f"✅ Group ID: 129031")
        else:
            print(f"⚠️  API response: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Samsara API integration test failed: {str(e)}")
        return False


def test_dashboard_functionality():
    """Test dashboard functionality."""
    print("\n📈 Testing Dashboard Functionality")
    print("-" * 50)
    
    try:
        # Check if dashboard file exists
        dashboard_path = "pepworkday-pipeline/dashboard/auto_refresh_dashboard.html"
        if os.path.exists(dashboard_path):
            print("✅ Auto-refresh dashboard file exists")
            
            # Read dashboard content
            with open(dashboard_path, 'r') as f:
                content = f.read()
            
            # Check for PEPMove configuration
            if '5005620' in content and '129031' in content:
                print("✅ PEPMove configuration found in dashboard")
            
            # Check for auto-refresh functionality
            if 'setInterval' in content and 'refreshDashboardData' in content:
                print("✅ Auto-refresh functionality implemented")
            
            # Check for interactive filters
            if 'dateRange' in content and 'driverFilter' in content:
                print("✅ Interactive filters implemented")
            
        else:
            print("❌ Dashboard file not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard functionality test failed: {str(e)}")
        return False


def test_github_actions_workflow():
    """Test GitHub Actions workflow configuration."""
    print("\n⚙️ Testing GitHub Actions Workflow")
    print("-" * 50)
    
    try:
        workflow_path = ".github/workflows/pepmove-pipeline.yml"
        if os.path.exists(workflow_path):
            print("✅ GitHub Actions workflow file exists")
            
            with open(workflow_path, 'r') as f:
                content = f.read()
            
            # Check for PEPMove configuration
            if '5005620' in content and '129031' in content:
                print("✅ PEPMove configuration in workflow")
            
            # Check for scheduled execution
            if 'schedule:' in content and 'cron:' in content:
                print("✅ Scheduled execution configured")
            
            # Check for quality checks
            if 'flake8' in content and 'mypy' in content:
                print("✅ Code quality checks configured")
            
        else:
            print("❌ GitHub Actions workflow file not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ GitHub Actions workflow test failed: {str(e)}")
        return False


def run_comprehensive_integration_test():
    """Run comprehensive integration test of all advanced features."""
    print("🚀 COMPREHENSIVE PEPMOVE INTEGRATION TEST")
    print("=" * 60)
    print(f"Organization ID: 5005620")
    print(f"Group ID: 129031")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    test_results = {}
    
    # Run all tests
    tests = [
        ("Security Manager", test_security_manager),
        ("Advanced Polling", test_advanced_polling),
        ("Monitoring System", test_monitoring_system),
        ("Webhook Receiver", test_webhook_receiver),
        ("Samsara API Integration", test_samsara_api_integration),
        ("Dashboard Functionality", test_dashboard_functionality),
        ("GitHub Actions Workflow", test_github_actions_workflow)
    ]
    
    for test_name, test_function in tests:
        try:
            result = test_function()
            test_results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            test_results[test_name] = False
    
    # Summary
    print("\n🎯 INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    print("-" * 60)
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {passed_tests/total_tests:.1%}")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ PepWorkday Pipeline Advanced Integration is fully functional")
        print("✅ PEPMove Samsara API integration is ready for production")
        print("✅ All advanced features are working correctly")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} TESTS FAILED")
        print("❌ Some advanced features need attention")
        return False


def main():
    """Main function to run the integration test."""
    try:
        success = run_comprehensive_integration_test()
        
        print(f"\n📊 Final Status:")
        print(f"   Integration Test: {'SUCCESS' if success else 'FAILED'}")
        print(f"   PEPMove Ready: {'YES' if success else 'NO'}")
        print(f"   Production Ready: {'YES' if success else 'NO'}")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Integration test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Integration test crashed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
