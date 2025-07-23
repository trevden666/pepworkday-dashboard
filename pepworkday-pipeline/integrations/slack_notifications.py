"""
Slack notifications module for the PepWorkday pipeline.

Chain of thought:
1. Support both Slack Bot API and Webhook methods for flexibility
2. Create rich, formatted messages with pipeline status and key metrics
3. Handle different notification types: success, error, warning, info
4. Include relevant data summaries and actionable information
5. Implement retry logic and error handling for reliable delivery
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


@dataclass
class NotificationData:
    """Container for notification data and metrics."""
    pipeline_status: str  # 'success', 'error', 'warning'
    message: str
    details: Dict[str, Any] = None
    metrics: Dict[str, Any] = None
    errors: List[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.details is None:
            self.details = {}
        if self.metrics is None:
            self.metrics = {}
        if self.errors is None:
            self.errors = []


class SlackNotificationError(Exception):
    """Custom exception for Slack notification errors."""
    pass


class SlackNotifier:
    """Slack notification client supporting both Bot API and Webhooks."""
    
    def __init__(
        self,
        bot_token: Optional[str] = None,
        webhook_url: Optional[str] = None,
        default_channel: str = "#automation-alerts"
    ):
        """
        Initialize Slack notifier.
        
        Args:
            bot_token: Slack Bot User OAuth Token
            webhook_url: Slack Incoming Webhook URL
            default_channel: Default channel for notifications
        """
        self.bot_token = bot_token
        self.webhook_url = webhook_url
        self.default_channel = default_channel
        self.client = None
        
        if not bot_token and not webhook_url:
            raise SlackNotificationError(
                "Either bot_token or webhook_url must be provided"
            )
        
        if bot_token:
            self.client = WebClient(token=bot_token)
            logger.info("Initialized Slack client with Bot API")
        else:
            logger.info("Initialized Slack client with Webhook")
    
    def send_pipeline_notification(
        self,
        notification_data: NotificationData,
        channel: Optional[str] = None
    ) -> bool:
        """
        Send a formatted pipeline notification to Slack.
        
        Args:
            notification_data: Notification data and metrics
            channel: Slack channel (uses default if not provided)
            
        Returns:
            bool: True if notification was sent successfully
        """
        channel = channel or self.default_channel
        
        try:
            # Create formatted message blocks
            blocks = self._create_message_blocks(notification_data)
            
            # Send via Bot API or Webhook
            if self.client:
                success = self._send_via_bot_api(blocks, channel)
            else:
                success = self._send_via_webhook(blocks, channel)
            
            if success:
                logger.info(f"Successfully sent Slack notification to {channel}")
            else:
                logger.error(f"Failed to send Slack notification to {channel}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending Slack notification: {str(e)}")
            return False
    
    def send_success_notification(
        self,
        message: str,
        metrics: Dict[str, Any] = None,
        channel: Optional[str] = None
    ) -> bool:
        """Send a success notification with metrics."""
        notification_data = NotificationData(
            pipeline_status='success',
            message=message,
            metrics=metrics or {}
        )
        return self.send_pipeline_notification(notification_data, channel)
    
    def send_error_notification(
        self,
        message: str,
        errors: List[str] = None,
        details: Dict[str, Any] = None,
        channel: Optional[str] = None
    ) -> bool:
        """Send an error notification with details."""
        notification_data = NotificationData(
            pipeline_status='error',
            message=message,
            errors=errors or [],
            details=details or {}
        )
        return self.send_pipeline_notification(notification_data, channel)
    
    def send_warning_notification(
        self,
        message: str,
        details: Dict[str, Any] = None,
        channel: Optional[str] = None
    ) -> bool:
        """Send a warning notification."""
        notification_data = NotificationData(
            pipeline_status='warning',
            message=message,
            details=details or {}
        )
        return self.send_pipeline_notification(notification_data, channel)
    
    def _create_message_blocks(self, data: NotificationData) -> List[Dict]:
        """Create Slack message blocks for rich formatting."""
        blocks = []
        
        # Header block with status emoji
        status_emoji = self._get_status_emoji(data.pipeline_status)
        header_text = f"{status_emoji} *PepWorkday Pipeline {data.pipeline_status.title()}*"
        
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"PepWorkday Pipeline {data.pipeline_status.title()}"
            }
        })
        
        # Main message block
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{status_emoji} {data.message}"
            }
        })
        
        # Metrics section (for success notifications)
        if data.metrics and data.pipeline_status == 'success':
            metrics_text = self._format_metrics(data.metrics)
            if metrics_text:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*📊 Pipeline Metrics:*\n{metrics_text}"
                    }
                })
        
        # Error details (for error notifications)
        if data.errors and data.pipeline_status == 'error':
            error_text = "\n".join([f"• {error}" for error in data.errors[:5]])  # Limit to 5 errors
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*❌ Errors:*\n{error_text}"
                }
            })
        
        # Additional details
        if data.details:
            details_text = self._format_details(data.details)
            if details_text:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*📋 Details:*\n{details_text}"
                    }
                })
        
        # Footer with timestamp
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"🕐 {data.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            ]
        })
        
        return blocks
    
    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for pipeline status."""
        emoji_map = {
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️'
        }
        return emoji_map.get(status, '📋')
    
    def _format_metrics(self, metrics: Dict[str, Any]) -> str:
        """Format metrics for display in Slack."""
        formatted_lines = []
        
        # Common metrics formatting
        metric_formatters = {
            'records_processed': lambda x: f"Records Processed: {x:,}",
            'records_inserted': lambda x: f"Records Inserted: {x:,}",
            'records_updated': lambda x: f"Records Updated: {x:,}",
            'match_rate': lambda x: f"Match Rate: {x:.1%}",
            'processing_time': lambda x: f"Processing Time: {x:.1f}s",
            'avg_miles_variance': lambda x: f"Avg Miles Variance: {x:+.1f}",
            'avg_stops_variance': lambda x: f"Avg Stops Variance: {x:+.1f}",
            'avg_idle_percentage': lambda x: f"Avg Idle Time: {x:.1f}%"
        }
        
        for key, value in metrics.items():
            if key in metric_formatters and value is not None:
                try:
                    formatted_lines.append(metric_formatters[key](value))
                except (ValueError, TypeError):
                    formatted_lines.append(f"{key.replace('_', ' ').title()}: {value}")
            elif value is not None:
                formatted_lines.append(f"{key.replace('_', ' ').title()}: {value}")
        
        return "\n".join(formatted_lines)
    
    def _format_details(self, details: Dict[str, Any]) -> str:
        """Format additional details for display."""
        formatted_lines = []
        
        for key, value in details.items():
            if isinstance(value, (list, dict)):
                value = json.dumps(value, indent=2)
            formatted_lines.append(f"{key.replace('_', ' ').title()}: {value}")
        
        return "\n".join(formatted_lines)
    
    def _send_via_bot_api(self, blocks: List[Dict], channel: str) -> bool:
        """Send notification via Slack Bot API."""
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text="PepWorkday Pipeline Notification"  # Fallback text
            )
            return response["ok"]
            
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending via Bot API: {str(e)}")
            return False
    
    def _send_via_webhook(self, blocks: List[Dict], channel: str) -> bool:
        """Send notification via Slack Webhook."""
        try:
            payload = {
                "channel": channel,
                "blocks": blocks,
                "text": "PepWorkday Pipeline Notification"
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=30
            )
            
            return response.status_code == 200
            
        except requests.RequestException as e:
            logger.error(f"Webhook request error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending via webhook: {str(e)}")
            return False


def create_pipeline_summary_metrics(
    total_records: int,
    processed_records: int,
    inserted_records: int,
    updated_records: int,
    processing_time: float,
    match_rate: Optional[float] = None,
    avg_miles_variance: Optional[float] = None,
    avg_stops_variance: Optional[float] = None,
    avg_idle_percentage: Optional[float] = None
) -> Dict[str, Any]:
    """
    Create a standardized metrics dictionary for pipeline notifications.
    
    Args:
        total_records: Total number of records in input
        processed_records: Number of records successfully processed
        inserted_records: Number of new records inserted
        updated_records: Number of existing records updated
        processing_time: Total processing time in seconds
        match_rate: Samsara data match rate (0.0 to 1.0)
        avg_miles_variance: Average miles variance
        avg_stops_variance: Average stops variance
        avg_idle_percentage: Average idle time percentage
        
    Returns:
        Dict containing formatted metrics
    """
    metrics = {
        'total_records': total_records,
        'records_processed': processed_records,
        'records_inserted': inserted_records,
        'records_updated': updated_records,
        'processing_time': processing_time
    }
    
    # Add optional metrics if provided
    if match_rate is not None:
        metrics['match_rate'] = match_rate
    if avg_miles_variance is not None:
        metrics['avg_miles_variance'] = avg_miles_variance
    if avg_stops_variance is not None:
        metrics['avg_stops_variance'] = avg_stops_variance
    if avg_idle_percentage is not None:
        metrics['avg_idle_percentage'] = avg_idle_percentage
    
    return metrics
