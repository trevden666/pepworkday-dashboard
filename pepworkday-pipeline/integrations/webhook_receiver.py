"""
Samsara Webhook Receiver for PepWorkday Pipeline.

This module implements a Flask-based webhook receiver that processes real-time
Samsara events and integrates them into the PepWorkday pipeline workflow.

Supported Events:
- Trip start/stop events
- Vehicle location updates
- Driver status changes
- Maintenance alerts
- Geofence entry/exit events

PepWorkday Configuration:
- Organization ID: 5005620
- Group ID: 129031
"""

import json
import logging
import hashlib
import hmac
from datetime import datetime
from typing import Dict, Any, Optional, List
from flask import Flask, request, jsonify, abort
import pandas as pd
from dataclasses import dataclass

from ..integrations.google_sheets import GoogleSheetsClient
from ..integrations.slack_notifications import SlackNotifier
from ..utils.samsara_api import vehicle_locations_to_dataframe
from ..config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class WebhookEvent:
    """Container for processed webhook event data."""
    event_type: str
    event_id: str
    timestamp: datetime
    organization_id: str
    group_id: str
    vehicle_id: Optional[str] = None
    driver_id: Optional[str] = None
    data: Dict[str, Any] = None
    processed: bool = False


class SamsaraWebhookReceiver:
    """Flask-based webhook receiver for Samsara events."""
    
    def __init__(
        self,
        webhook_secret: Optional[str] = None,
        enable_signature_verification: bool = True,
        auto_process_events: bool = True
    ):
        """
        Initialize the webhook receiver.
        
        Args:
            webhook_secret: Secret for webhook signature verification
            enable_signature_verification: Whether to verify webhook signatures
            auto_process_events: Whether to automatically process events
        """
        self.app = Flask(__name__)
        self.webhook_secret = webhook_secret
        self.enable_signature_verification = enable_signature_verification
        self.auto_process_events = auto_process_events
        
        # Initialize integrations
        self.sheets_client = None
        self.slack_notifier = None
        
        # Event handlers registry
        self.event_handlers = {
            'trip': self._handle_trip_event,
            'vehicle': self._handle_vehicle_event,
            'driver': self._handle_driver_event,
            'geofence': self._handle_geofence_event,
            'maintenance': self._handle_maintenance_event
        }
        
        # Setup Flask routes
        self._setup_routes()
        
        logger.info("Initialized Samsara webhook receiver for PepWorkday")
    
    def _setup_routes(self):
        """Setup Flask routes for webhook endpoints."""
        
        @self.app.route('/webhook/samsara', methods=['POST'])
        def receive_webhook():
            """Main webhook endpoint for Samsara events."""
            try:
                # Verify webhook signature if enabled
                if self.enable_signature_verification:
                    if not self._verify_signature(request):
                        logger.warning("Webhook signature verification failed")
                        abort(401)
                
                # Parse webhook payload
                payload = request.get_json()
                if not payload:
                    logger.error("Empty webhook payload received")
                    abort(400)
                
                # Process the webhook event
                event = self._parse_webhook_event(payload)
                
                if self.auto_process_events:
                    result = self._process_event(event)
                    return jsonify({
                        'status': 'success',
                        'event_id': event.event_id,
                        'processed': result
                    })
                else:
                    return jsonify({
                        'status': 'received',
                        'event_id': event.event_id,
                        'message': 'Event queued for processing'
                    })
                
            except Exception as e:
                logger.error(f"Webhook processing error: {str(e)}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/webhook/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'service': 'PepWorkday Samsara Webhook Receiver',
                'organization_id': '5005620',
                'group_id': '129031',
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/webhook/stats', methods=['GET'])
        def webhook_stats():
            """Webhook statistics endpoint."""
            return jsonify({
                'supported_events': list(self.event_handlers.keys()),
                'auto_processing': self.auto_process_events,
                'signature_verification': self.enable_signature_verification,
                'integrations': {
                    'google_sheets': self.sheets_client is not None,
                    'slack': self.slack_notifier is not None
                }
            })
    
    def _verify_signature(self, request) -> bool:
        """Verify webhook signature for security."""
        if not self.webhook_secret:
            return True  # Skip verification if no secret configured
        
        signature = request.headers.get('X-Samsara-Signature')
        if not signature:
            return False
        
        # Calculate expected signature
        payload = request.get_data()
        expected_signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, f"sha256={expected_signature}")
    
    def _parse_webhook_event(self, payload: Dict[str, Any]) -> WebhookEvent:
        """Parse webhook payload into structured event."""
        event_type = payload.get('eventType', 'unknown')
        event_id = payload.get('eventId', f"evt_{datetime.now().timestamp()}")
        timestamp_str = payload.get('eventTime', datetime.now().isoformat())
        
        # Parse timestamp
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            timestamp = datetime.now()
        
        # Extract PepWorkday context
        organization_id = payload.get('organizationId', '5005620')
        group_id = payload.get('groupId', '129031')
        
        # Extract entity IDs
        vehicle_id = payload.get('vehicleId')
        driver_id = payload.get('driverId')
        
        return WebhookEvent(
            event_type=event_type,
            event_id=event_id,
            timestamp=timestamp,
            organization_id=organization_id,
            group_id=group_id,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            data=payload
        )
    
    def _process_event(self, event: WebhookEvent) -> bool:
        """Process a webhook event based on its type."""
        try:
            logger.info(f"Processing {event.event_type} event {event.event_id}")
            
            # Determine event category
            event_category = self._categorize_event(event.event_type)
            
            # Get appropriate handler
            handler = self.event_handlers.get(event_category)
            if not handler:
                logger.warning(f"No handler for event category: {event_category}")
                return False
            
            # Process the event
            result = handler(event)
            
            if result:
                event.processed = True
                logger.info(f"Successfully processed event {event.event_id}")
            else:
                logger.error(f"Failed to process event {event.event_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing event {event.event_id}: {str(e)}")
            return False
    
    def _categorize_event(self, event_type: str) -> str:
        """Categorize event type for handler selection."""
        event_type_lower = event_type.lower()
        
        if any(keyword in event_type_lower for keyword in ['trip', 'route']):
            return 'trip'
        elif any(keyword in event_type_lower for keyword in ['vehicle', 'location']):
            return 'vehicle'
        elif any(keyword in event_type_lower for keyword in ['driver']):
            return 'driver'
        elif any(keyword in event_type_lower for keyword in ['geofence', 'fence']):
            return 'geofence'
        elif any(keyword in event_type_lower for keyword in ['maintenance', 'alert']):
            return 'maintenance'
        else:
            return 'unknown'
    
    def _handle_trip_event(self, event: WebhookEvent) -> bool:
        """Handle trip-related events (start, stop, etc.)."""
        try:
            trip_data = event.data.get('trip', {})
            
            # Extract trip information
            trip_info = {
                'event_id': event.event_id,
                'event_type': event.event_type,
                'timestamp': event.timestamp.isoformat(),
                'organization_id': event.organization_id,
                'group_id': event.group_id,
                'vehicle_id': event.vehicle_id,
                'driver_id': event.driver_id,
                'trip_id': trip_data.get('id'),
                'trip_status': trip_data.get('status'),
                'start_location': trip_data.get('startLocation'),
                'end_location': trip_data.get('endLocation'),
                'distance_miles': trip_data.get('distanceMiles'),
                'duration_ms': trip_data.get('durationMs')
            }
            
            # Update Google Sheets if configured
            if self.sheets_client:
                self._update_sheets_with_trip_data(trip_info)
            
            # Send Slack notification for significant events
            if self.slack_notifier and event.event_type in ['tripStarted', 'tripCompleted']:
                self._send_trip_notification(trip_info)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling trip event: {str(e)}")
            return False
    
    def _handle_vehicle_event(self, event: WebhookEvent) -> bool:
        """Handle vehicle-related events (location updates, etc.)."""
        try:
            vehicle_data = event.data.get('vehicle', {})
            location_data = vehicle_data.get('location', {})
            
            # Create location update record
            location_info = {
                'event_id': event.event_id,
                'timestamp': event.timestamp.isoformat(),
                'organization_id': event.organization_id,
                'group_id': event.group_id,
                'vehicle_id': event.vehicle_id,
                'latitude': location_data.get('latitude'),
                'longitude': location_data.get('longitude'),
                'speed_mph': location_data.get('speed'),
                'heading': location_data.get('heading'),
                'address': location_data.get('reverseGeo', {}).get('formattedLocation')
            }
            
            # Update real-time location tracking
            if self.sheets_client:
                self._update_sheets_with_location_data(location_info)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling vehicle event: {str(e)}")
            return False
    
    def _handle_driver_event(self, event: WebhookEvent) -> bool:
        """Handle driver-related events."""
        logger.info(f"Processing driver event: {event.event_type}")
        # Implement driver event handling logic
        return True
    
    def _handle_geofence_event(self, event: WebhookEvent) -> bool:
        """Handle geofence entry/exit events."""
        logger.info(f"Processing geofence event: {event.event_type}")
        # Implement geofence event handling logic
        return True
    
    def _handle_maintenance_event(self, event: WebhookEvent) -> bool:
        """Handle maintenance and alert events."""
        logger.info(f"Processing maintenance event: {event.event_type}")
        # Implement maintenance event handling logic
        return True
    
    def _update_sheets_with_trip_data(self, trip_info: Dict[str, Any]):
        """Update Google Sheets with trip event data."""
        try:
            # Convert to DataFrame
            df = pd.DataFrame([trip_info])
            
            # Update the TripEvents worksheet
            self.sheets_client.upsert_data(
                worksheet_name="TripEvents",
                data=df,
                key_column="event_id"
            )
            
            logger.info(f"Updated Google Sheets with trip event {trip_info['event_id']}")
            
        except Exception as e:
            logger.error(f"Error updating sheets with trip data: {str(e)}")
    
    def _update_sheets_with_location_data(self, location_info: Dict[str, Any]):
        """Update Google Sheets with location event data."""
        try:
            # Convert to DataFrame
            df = pd.DataFrame([location_info])
            
            # Update the LocationUpdates worksheet
            self.sheets_client.upsert_data(
                worksheet_name="LocationUpdates",
                data=df,
                key_column="event_id"
            )
            
            logger.info(f"Updated Google Sheets with location event {location_info['event_id']}")
            
        except Exception as e:
            logger.error(f"Error updating sheets with location data: {str(e)}")
    
    def _send_trip_notification(self, trip_info: Dict[str, Any]):
        """Send Slack notification for trip events."""
        try:
            event_type = trip_info['event_type']
            vehicle_id = trip_info['vehicle_id']
            
            if event_type == 'tripStarted':
                message = f"🚛 Trip Started - Vehicle {vehicle_id}"
            elif event_type == 'tripCompleted':
                distance = trip_info.get('distance_miles', 'Unknown')
                message = f"🏁 Trip Completed - Vehicle {vehicle_id} ({distance} miles)"
            else:
                message = f"📍 Trip Event - Vehicle {vehicle_id}: {event_type}"
            
            self.slack_notifier.send_success_notification(
                message=message,
                metrics=trip_info
            )
            
        except Exception as e:
            logger.error(f"Error sending trip notification: {str(e)}")
    
    def initialize_integrations(self):
        """Initialize Google Sheets and Slack integrations."""
        try:
            # Initialize Google Sheets client
            self.sheets_client = GoogleSheetsClient(
                credentials_path=settings.google_sheets.credentials_path,
                spreadsheet_id=settings.google_sheets.spreadsheet_id
            )
            logger.info("Initialized Google Sheets integration")
            
            # Initialize Slack notifier
            self.slack_notifier = SlackNotifier(
                bot_token=settings.slack.bot_token,
                webhook_url=settings.slack.webhook_url,
                default_channel=settings.slack.channel
            )
            logger.info("Initialized Slack integration")
            
        except Exception as e:
            logger.error(f"Error initializing integrations: {str(e)}")
    
    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """Run the webhook receiver Flask app."""
        logger.info(f"Starting PepWorkday webhook receiver on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


def create_webhook_receiver() -> SamsaraWebhookReceiver:
    """Create and configure a webhook receiver for PepWorkday."""
    receiver = SamsaraWebhookReceiver(
        webhook_secret=getattr(settings, 'webhook_secret', None),
        enable_signature_verification=True,
        auto_process_events=True
    )
    
    # Initialize integrations
    receiver.initialize_integrations()
    
    return receiver


if __name__ == "__main__":
    # Run the webhook receiver
    receiver = create_webhook_receiver()
    receiver.run(debug=True)
