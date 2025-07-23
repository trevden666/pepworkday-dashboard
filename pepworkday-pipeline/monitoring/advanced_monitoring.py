"""
Advanced Monitoring and Error Handling for PepWorkday Pipeline.

This module provides comprehensive monitoring, alerting, and error handling
capabilities for the PepWorkday pipeline with PEPMove integration.

Features:
- Structured logging with contextual information
- Real-time metrics collection and analysis
- Intelligent alerting with escalation
- Error categorization and automated recovery
- Performance monitoring and optimization suggestions
- Integration health checks and diagnostics

PepWorkday Configuration:
- Organization ID: 5005620
- Group ID: 129031
"""

import logging
import json
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict, deque
import psutil
import requests

from ..integrations.slack_notifications import SlackNotifier
from ..config.settings import settings

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categorization for automated handling."""
    API_ERROR = "api_error"
    AUTHENTICATION_ERROR = "auth_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    DATA_VALIDATION_ERROR = "data_validation_error"
    NETWORK_ERROR = "network_error"
    SYSTEM_ERROR = "system_error"
    CONFIGURATION_ERROR = "config_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class Alert:
    """Container for alert information."""
    alert_id: str
    severity: AlertSeverity
    category: ErrorCategory
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    escalated: bool = False


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    timestamp: datetime = field(default_factory=datetime.now)
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    api_response_times: List[float] = field(default_factory=list)
    active_connections: int = 0
    error_rate: float = 0.0
    throughput: float = 0.0  # records per second


class AdvancedMonitor:
    """Advanced monitoring system for PepWorkday pipeline."""
    
    def __init__(
        self,
        enable_real_time_monitoring: bool = True,
        metrics_retention_hours: int = 24,
        alert_cooldown_minutes: int = 15
    ):
        """
        Initialize the advanced monitoring system.
        
        Args:
            enable_real_time_monitoring: Enable real-time monitoring
            metrics_retention_hours: How long to retain metrics
            alert_cooldown_minutes: Cooldown period between similar alerts
        """
        self.enable_real_time_monitoring = enable_real_time_monitoring
        self.metrics_retention_hours = metrics_retention_hours
        self.alert_cooldown_minutes = alert_cooldown_minutes
        
        # Monitoring data
        self.metrics_history: deque = deque(maxlen=1000)
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.error_counts: Dict[ErrorCategory, int] = defaultdict(int)
        
        # Alert cooldowns
        self.alert_cooldowns: Dict[str, datetime] = {}
        
        # Integration clients
        self.slack_notifier: Optional[SlackNotifier] = None
        
        # Monitoring thread
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
        self._initialize_integrations()
        
        if self.enable_real_time_monitoring:
            self._start_monitoring_thread()
    
    def _initialize_integrations(self):
        """Initialize monitoring integrations."""
        try:
            self.slack_notifier = SlackNotifier(
                bot_token=settings.slack.bot_token,
                webhook_url=settings.slack.webhook_url,
                default_channel=settings.slack.channel
            )
            self.logger.info("Initialized monitoring integrations")
        except Exception as e:
            self.logger.error(f"Failed to initialize monitoring integrations: {str(e)}")
    
    def _start_monitoring_thread(self):
        """Start the real-time monitoring thread."""
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("Started real-time monitoring thread")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Collect performance metrics
                metrics = self._collect_performance_metrics()
                self.metrics_history.append(metrics)
                
                # Check for performance issues
                self._check_performance_thresholds(metrics)
                
                # Clean up old data
                self._cleanup_old_data()
                
                # Sleep for monitoring interval
                time.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(60)  # Wait longer on error
    
    def _collect_performance_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics."""
        try:
            # System metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            memory_usage = memory_info.percent
            
            # Network connections
            connections = psutil.net_connections()
            active_connections = len([c for c in connections if c.status == 'ESTABLISHED'])
            
            return PerformanceMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                active_connections=active_connections
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting performance metrics: {str(e)}")
            return PerformanceMetrics()
    
    def _check_performance_thresholds(self, metrics: PerformanceMetrics):
        """Check performance metrics against thresholds."""
        # CPU usage threshold
        if metrics.cpu_usage > 80:
            self.create_alert(
                severity=AlertSeverity.HIGH,
                category=ErrorCategory.SYSTEM_ERROR,
                title="High CPU Usage",
                message=f"CPU usage is {metrics.cpu_usage:.1f}%",
                context={'cpu_usage': metrics.cpu_usage}
            )
        
        # Memory usage threshold
        if metrics.memory_usage > 85:
            self.create_alert(
                severity=AlertSeverity.HIGH,
                category=ErrorCategory.SYSTEM_ERROR,
                title="High Memory Usage",
                message=f"Memory usage is {metrics.memory_usage:.1f}%",
                context={'memory_usage': metrics.memory_usage}
            )
    
    def create_alert(
        self,
        severity: AlertSeverity,
        category: ErrorCategory,
        title: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        auto_resolve: bool = False
    ) -> str:
        """
        Create a new alert.
        
        Args:
            severity: Alert severity level
            category: Error category
            title: Alert title
            message: Alert message
            context: Additional context information
            auto_resolve: Whether to auto-resolve the alert
            
        Returns:
            Alert ID
        """
        alert_id = f"alert_{int(time.time())}_{category.value}"
        
        # Check cooldown
        cooldown_key = f"{category.value}_{title}"
        if cooldown_key in self.alert_cooldowns:
            last_alert = self.alert_cooldowns[cooldown_key]
            if datetime.now() - last_alert < timedelta(minutes=self.alert_cooldown_minutes):
                self.logger.debug(f"Alert {cooldown_key} is in cooldown period")
                return alert_id
        
        # Create alert
        alert = Alert(
            alert_id=alert_id,
            severity=severity,
            category=category,
            title=title,
            message=message,
            context=context or {}
        )
        
        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        self.error_counts[category] += 1
        
        # Set cooldown
        self.alert_cooldowns[cooldown_key] = datetime.now()
        
        # Send notification
        self._send_alert_notification(alert)
        
        # Auto-resolve if requested
        if auto_resolve:
            self.resolve_alert(alert_id)
        
        self.logger.warning(f"Created alert {alert_id}: {title}")
        return alert_id
    
    def resolve_alert(self, alert_id: str, resolution_message: Optional[str] = None):
        """Resolve an active alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolution_time = datetime.now()
            
            if resolution_message:
                alert.context['resolution_message'] = resolution_message
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            self.logger.info(f"Resolved alert {alert_id}")
    
    def _send_alert_notification(self, alert: Alert):
        """Send alert notification via Slack."""
        if not self.slack_notifier:
            return
        
        try:
            # Determine emoji based on severity
            severity_emojis = {
                AlertSeverity.LOW: "ℹ️",
                AlertSeverity.MEDIUM: "⚠️",
                AlertSeverity.HIGH: "🚨",
                AlertSeverity.CRITICAL: "🔥"
            }
            
            emoji = severity_emojis.get(alert.severity, "⚠️")
            
            # Create notification message
            message = f"{emoji} **PepWorkday Alert - {alert.severity.value.upper()}**\n"
            message += f"**{alert.title}**\n"
            message += f"{alert.message}\n"
            message += f"Category: {alert.category.value}\n"
            message += f"Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            message += f"Organization: 5005620 | Group: 129031"
            
            # Add context if available
            if alert.context:
                context_str = json.dumps(alert.context, indent=2)
                message += f"\n**Context:**\n```{context_str}```"
            
            # Send notification based on severity
            if alert.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
                self.slack_notifier.send_error_notification(
                    message=alert.title,
                    errors=[alert.message],
                    details=alert.context
                )
            else:
                self.slack_notifier.send_warning_notification(
                    message=alert.title,
                    details=alert.context
                )
            
        except Exception as e:
            self.logger.error(f"Failed to send alert notification: {str(e)}")
    
    def log_api_call(
        self,
        endpoint: str,
        method: str,
        response_time: float,
        status_code: int,
        error: Optional[str] = None
    ):
        """Log API call metrics."""
        # Add to metrics history
        if self.metrics_history:
            latest_metrics = self.metrics_history[-1]
            latest_metrics.api_response_times.append(response_time)
        
        # Log the call
        log_data = {
            'endpoint': endpoint,
            'method': method,
            'response_time': response_time,
            'status_code': status_code,
            'timestamp': datetime.now().isoformat(),
            'organization_id': '5005620',
            'group_id': '129031'
        }
        
        if error:
            log_data['error'] = error
            self.logger.error(f"API call failed: {json.dumps(log_data)}")
        else:
            self.logger.info(f"API call completed: {json.dumps(log_data)}")
        
        # Check for slow API calls
        if response_time > 10.0:  # 10 seconds threshold
            self.create_alert(
                severity=AlertSeverity.MEDIUM,
                category=ErrorCategory.API_ERROR,
                title="Slow API Response",
                message=f"API call to {endpoint} took {response_time:.2f} seconds",
                context=log_data,
                auto_resolve=True
            )
    
    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        category: Optional[ErrorCategory] = None
    ):
        """Log and categorize errors."""
        # Categorize error if not provided
        if not category:
            category = self._categorize_error(error)
        
        # Create error context
        error_context = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'timestamp': datetime.now().isoformat(),
            'organization_id': '5005620',
            'group_id': '129031'
        }
        
        if context:
            error_context.update(context)
        
        # Log structured error
        self.logger.error(f"Categorized error: {json.dumps(error_context)}")
        
        # Create alert for significant errors
        severity = self._determine_error_severity(category, error)
        
        if severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
            self.create_alert(
                severity=severity,
                category=category,
                title=f"{category.value.replace('_', ' ').title()}",
                message=str(error),
                context=error_context
            )
    
    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Automatically categorize errors."""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        if 'auth' in error_str or 'token' in error_str or '401' in error_str:
            return ErrorCategory.AUTHENTICATION_ERROR
        elif 'rate limit' in error_str or '429' in error_str:
            return ErrorCategory.RATE_LIMIT_ERROR
        elif 'network' in error_str or 'connection' in error_str or 'timeout' in error_str:
            return ErrorCategory.NETWORK_ERROR
        elif 'validation' in error_str or 'schema' in error_str:
            return ErrorCategory.DATA_VALIDATION_ERROR
        elif 'config' in error_str or 'setting' in error_str:
            return ErrorCategory.CONFIGURATION_ERROR
        elif 'api' in error_str or 'http' in error_str:
            return ErrorCategory.API_ERROR
        elif 'memory' in error_str or 'cpu' in error_str or 'disk' in error_str:
            return ErrorCategory.SYSTEM_ERROR
        else:
            return ErrorCategory.UNKNOWN_ERROR
    
    def _determine_error_severity(self, category: ErrorCategory, error: Exception) -> AlertSeverity:
        """Determine error severity based on category and error details."""
        critical_categories = [ErrorCategory.AUTHENTICATION_ERROR, ErrorCategory.SYSTEM_ERROR]
        high_categories = [ErrorCategory.API_ERROR, ErrorCategory.CONFIGURATION_ERROR]
        medium_categories = [ErrorCategory.NETWORK_ERROR, ErrorCategory.DATA_VALIDATION_ERROR]
        
        if category in critical_categories:
            return AlertSeverity.CRITICAL
        elif category in high_categories:
            return AlertSeverity.HIGH
        elif category in medium_categories:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW
    
    def _cleanup_old_data(self):
        """Clean up old monitoring data."""
        cutoff_time = datetime.now() - timedelta(hours=self.metrics_retention_hours)
        
        # Clean up alert history
        self.alert_history = [
            alert for alert in self.alert_history
            if alert.timestamp > cutoff_time
        ]
        
        # Clean up cooldowns
        self.alert_cooldowns = {
            key: timestamp for key, timestamp in self.alert_cooldowns.items()
            if timestamp > cutoff_time
        }
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get comprehensive monitoring summary."""
        return {
            'timestamp': datetime.now().isoformat(),
            'organization_id': '5005620',
            'group_id': '129031',
            'active_alerts': len(self.active_alerts),
            'total_alerts_today': len([
                a for a in self.alert_history
                if a.timestamp > datetime.now() - timedelta(days=1)
            ]),
            'error_counts': dict(self.error_counts),
            'performance_metrics': {
                'latest_cpu_usage': self.metrics_history[-1].cpu_usage if self.metrics_history else 0,
                'latest_memory_usage': self.metrics_history[-1].memory_usage if self.metrics_history else 0,
                'avg_api_response_time': sum(
                    sum(m.api_response_times) / len(m.api_response_times)
                    for m in self.metrics_history if m.api_response_times
                ) / len(self.metrics_history) if self.metrics_history else 0
            },
            'monitoring_active': self.monitoring_active
        }
    
    def stop_monitoring(self):
        """Stop the monitoring system."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("Stopped monitoring system")


# Global monitor instance
monitor = AdvancedMonitor()


def log_api_call(endpoint: str, method: str, response_time: float, status_code: int, error: Optional[str] = None):
    """Convenience function to log API calls."""
    monitor.log_api_call(endpoint, method, response_time, status_code, error)


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None, category: Optional[ErrorCategory] = None):
    """Convenience function to log errors."""
    monitor.log_error(error, context, category)


def create_alert(severity: AlertSeverity, category: ErrorCategory, title: str, message: str, context: Optional[Dict[str, Any]] = None):
    """Convenience function to create alerts."""
    return monitor.create_alert(severity, category, title, message, context)
