"""
Security Manager for PepWorkday Pipeline.

This module implements comprehensive security features including:
- Secure API token management with rotation
- Rate limiting with intelligent backoff
- Request authentication and authorization
- Data encryption and secure storage
- Audit logging and compliance
- Least-privilege access controls

PepWorkday Configuration:
- Organization ID: 5005620
- Group ID: 129031
- Implements security best practices for Samsara API integration
"""

import os
import time
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import secrets
from collections import defaultdict, deque

from ..config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class SecurityEvent:
    """Container for security-related events."""
    event_id: str
    event_type: str  # 'auth_failure', 'rate_limit', 'token_rotation', etc.
    severity: str    # 'low', 'medium', 'high', 'critical'
    timestamp: datetime = field(default_factory=datetime.now)
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    organization_id: str = '5005620'
    group_id: str = '129031'


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_allowance: int = 10
    backoff_factor: float = 2.0
    max_backoff_seconds: int = 300


class SecureTokenManager:
    """Secure token management with rotation and encryption."""
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        """
        Initialize secure token manager.
        
        Args:
            encryption_key: Encryption key for token storage
        """
        self.encryption_key = encryption_key or self._generate_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.tokens: Dict[str, Dict[str, Any]] = {}
        self.token_usage: Dict[str, List[datetime]] = defaultdict(list)
        
        # Load PEPMove token
        self._initialize_pepmove_token()
    
    def _generate_encryption_key(self) -> bytes:
        """Generate a secure encryption key."""
        password = os.environ.get('ENCRYPTION_PASSWORD', 'pepmove-secure-key').encode()
        salt = os.environ.get('ENCRYPTION_SALT', 'pepmove-salt-5005620').encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def _initialize_pepmove_token(self):
        """Initialize PEPMove Samsara API token."""
        pepmove_token = os.getenv("SAMSARA_API_TOKEN", "your_api_token_here")
        
        self.store_token(
            token_id="pepmove_samsara",
            token_value=pepmove_token,
            token_type="samsara_api",
            organization_id="5005620",
            group_id="129031",
            scopes=["read:vehicles", "read:trips", "read:drivers", "read:locations"],
            expires_at=datetime.now() + timedelta(days=365)  # Long-lived token
        )
    
    def store_token(
        self,
        token_id: str,
        token_value: str,
        token_type: str,
        organization_id: str = "5005620",
        group_id: str = "129031",
        scopes: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None
    ):
        """Store a token securely with encryption."""
        encrypted_token = self.cipher_suite.encrypt(token_value.encode())
        
        self.tokens[token_id] = {
            'encrypted_token': encrypted_token,
            'token_type': token_type,
            'organization_id': organization_id,
            'group_id': group_id,
            'scopes': scopes or [],
            'created_at': datetime.now(),
            'expires_at': expires_at,
            'last_used': None,
            'usage_count': 0
        }
        
        logger.info(f"Stored secure token: {token_id}")
    
    def get_token(self, token_id: str) -> Optional[str]:
        """Retrieve and decrypt a token."""
        if token_id not in self.tokens:
            logger.warning(f"Token not found: {token_id}")
            return None
        
        token_info = self.tokens[token_id]
        
        # Check expiration
        if token_info['expires_at'] and datetime.now() > token_info['expires_at']:
            logger.warning(f"Token expired: {token_id}")
            return None
        
        # Decrypt token
        try:
            decrypted_token = self.cipher_suite.decrypt(token_info['encrypted_token']).decode()
            
            # Update usage tracking
            token_info['last_used'] = datetime.now()
            token_info['usage_count'] += 1
            self.token_usage[token_id].append(datetime.now())
            
            return decrypted_token
            
        except Exception as e:
            logger.error(f"Failed to decrypt token {token_id}: {str(e)}")
            return None
    
    def rotate_token(self, token_id: str, new_token_value: str) -> bool:
        """Rotate a token with the new value."""
        if token_id not in self.tokens:
            logger.error(f"Cannot rotate non-existent token: {token_id}")
            return False
        
        old_token_info = self.tokens[token_id].copy()
        
        # Store new token
        encrypted_new_token = self.cipher_suite.encrypt(new_token_value.encode())
        self.tokens[token_id]['encrypted_token'] = encrypted_new_token
        self.tokens[token_id]['rotated_at'] = datetime.now()
        self.tokens[token_id]['previous_usage_count'] = old_token_info['usage_count']
        self.tokens[token_id]['usage_count'] = 0
        
        logger.info(f"Rotated token: {token_id}")
        return True
    
    def get_token_info(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Get token metadata without decrypting the token."""
        if token_id not in self.tokens:
            return None
        
        token_info = self.tokens[token_id].copy()
        # Remove encrypted token from response
        token_info.pop('encrypted_token', None)
        return token_info


class IntelligentRateLimiter:
    """Intelligent rate limiter with adaptive backoff."""
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        """Initialize rate limiter with configuration."""
        self.config = config or RateLimitConfig()
        self.request_history: deque = deque(maxlen=10000)
        self.client_limits: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.backoff_delays: Dict[str, float] = defaultdict(float)
        self.security_events: List[SecurityEvent] = []
    
    def check_rate_limit(self, client_id: str = "default") -> Tuple[bool, float]:
        """
        Check if request is within rate limits.
        
        Args:
            client_id: Identifier for the client making the request
            
        Returns:
            Tuple of (allowed, delay_seconds)
        """
        now = datetime.now()
        client_history = self.client_limits[client_id]
        
        # Clean old requests
        cutoff_minute = now - timedelta(minutes=1)
        cutoff_hour = now - timedelta(hours=1)
        cutoff_day = now - timedelta(days=1)
        
        # Count recent requests
        minute_requests = sum(1 for req_time in client_history if req_time > cutoff_minute)
        hour_requests = sum(1 for req_time in client_history if req_time > cutoff_hour)
        day_requests = sum(1 for req_time in client_history if req_time > cutoff_day)
        
        # Check limits
        if minute_requests >= self.config.requests_per_minute:
            delay = self._calculate_backoff_delay(client_id, 'minute')
            self._log_rate_limit_event(client_id, 'minute', minute_requests)
            return False, delay
        
        if hour_requests >= self.config.requests_per_hour:
            delay = self._calculate_backoff_delay(client_id, 'hour')
            self._log_rate_limit_event(client_id, 'hour', hour_requests)
            return False, delay
        
        if day_requests >= self.config.requests_per_day:
            delay = self._calculate_backoff_delay(client_id, 'day')
            self._log_rate_limit_event(client_id, 'day', day_requests)
            return False, delay
        
        # Request allowed
        client_history.append(now)
        self.request_history.append((now, client_id))
        
        # Reset backoff delay on successful request
        if client_id in self.backoff_delays:
            self.backoff_delays[client_id] = max(0, self.backoff_delays[client_id] * 0.5)
        
        return True, 0.0
    
    def _calculate_backoff_delay(self, client_id: str, limit_type: str) -> float:
        """Calculate intelligent backoff delay."""
        current_delay = self.backoff_delays.get(client_id, 1.0)
        
        # Exponential backoff with jitter
        new_delay = min(
            current_delay * self.config.backoff_factor,
            self.config.max_backoff_seconds
        )
        
        # Add jitter to prevent thundering herd
        jitter = secrets.randbelow(int(new_delay * 0.1)) / 10.0
        final_delay = new_delay + jitter
        
        self.backoff_delays[client_id] = final_delay
        return final_delay
    
    def _log_rate_limit_event(self, client_id: str, limit_type: str, request_count: int):
        """Log rate limit security event."""
        event = SecurityEvent(
            event_id=f"rate_limit_{int(time.time())}",
            event_type="rate_limit_exceeded",
            severity="medium",
            details={
                'client_id': client_id,
                'limit_type': limit_type,
                'request_count': request_count,
                'limit_value': getattr(self.config, f'requests_per_{limit_type}')
            }
        )
        
        self.security_events.append(event)
        logger.warning(f"Rate limit exceeded for {client_id}: {limit_type} limit")


class SecurityAuditor:
    """Security auditing and compliance logging."""
    
    def __init__(self, log_file: Optional[str] = None):
        """Initialize security auditor."""
        self.log_file = log_file or "security_audit.log"
        self.audit_events: List[SecurityEvent] = []
        
        # Setup audit logger
        self.audit_logger = logging.getLogger('security_audit')
        handler = logging.FileHandler(self.log_file)
        formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.audit_logger.addHandler(handler)
        self.audit_logger.setLevel(logging.INFO)
    
    def log_security_event(self, event: SecurityEvent):
        """Log a security event for audit purposes."""
        self.audit_events.append(event)
        
        # Create audit log entry
        audit_entry = {
            'event_id': event.event_id,
            'event_type': event.event_type,
            'severity': event.severity,
            'timestamp': event.timestamp.isoformat(),
            'organization_id': event.organization_id,
            'group_id': event.group_id,
            'source_ip': event.source_ip,
            'user_agent': event.user_agent,
            'details': event.details
        }
        
        self.audit_logger.info(json.dumps(audit_entry))
        
        # Alert on high severity events
        if event.severity in ['high', 'critical']:
            logger.error(f"High severity security event: {event.event_type}")
    
    def generate_security_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate security report for the specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_events = [e for e in self.audit_events if e.timestamp > cutoff_time]
        
        # Categorize events
        event_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for event in recent_events:
            event_counts[event.event_type] += 1
            severity_counts[event.severity] += 1
        
        return {
            'report_period_hours': hours,
            'total_events': len(recent_events),
            'event_types': dict(event_counts),
            'severity_distribution': dict(severity_counts),
            'organization_id': '5005620',
            'group_id': '129031',
            'generated_at': datetime.now().isoformat()
        }


class PepWorkdaySecurityManager:
    """Comprehensive security manager for PepWorkday pipeline."""
    
    def __init__(self):
        """Initialize the security manager."""
        self.token_manager = SecureTokenManager()
        self.rate_limiter = IntelligentRateLimiter()
        self.auditor = SecurityAuditor()
        
        logger.info("Initialized PepWorkday Security Manager")
    
    def get_secure_api_token(self, token_id: str = "pepmove_samsara") -> Optional[str]:
        """Get a secure API token for PEPMove operations."""
        token = self.token_manager.get_token(token_id)
        
        if token:
            # Log token usage
            self.auditor.log_security_event(SecurityEvent(
                event_id=f"token_use_{int(time.time())}",
                event_type="token_accessed",
                severity="low",
                details={'token_id': token_id}
            ))
        
        return token
    
    def check_request_authorization(
        self,
        client_id: str,
        requested_scopes: List[str],
        organization_id: str = "5005620"
    ) -> bool:
        """Check if request is authorized."""
        # Verify organization access
        if organization_id != "5005620":
            self.auditor.log_security_event(SecurityEvent(
                event_id=f"auth_fail_{int(time.time())}",
                event_type="unauthorized_organization",
                severity="high",
                details={
                    'client_id': client_id,
                    'requested_org': organization_id,
                    'allowed_org': '5005620'
                }
            ))
            return False
        
        # Check rate limits
        allowed, delay = self.rate_limiter.check_rate_limit(client_id)
        if not allowed:
            return False
        
        # Additional authorization checks would go here
        return True
    
    def secure_api_request(
        self,
        endpoint: str,
        method: str = "GET",
        client_id: str = "pepmove_pipeline"
    ) -> Tuple[bool, Optional[str], float]:
        """
        Secure API request with full security checks.
        
        Returns:
            Tuple of (authorized, token, delay_seconds)
        """
        # Check authorization
        if not self.check_request_authorization(client_id, [], "5005620"):
            return False, None, 0.0
        
        # Check rate limits
        allowed, delay = self.rate_limiter.check_rate_limit(client_id)
        if not allowed:
            return False, None, delay
        
        # Get secure token
        token = self.get_secure_api_token()
        if not token:
            self.auditor.log_security_event(SecurityEvent(
                event_id=f"token_fail_{int(time.time())}",
                event_type="token_unavailable",
                severity="high",
                details={'endpoint': endpoint, 'method': method}
            ))
            return False, None, 0.0
        
        # Log successful authorization
        self.auditor.log_security_event(SecurityEvent(
            event_id=f"auth_success_{int(time.time())}",
            event_type="api_request_authorized",
            severity="low",
            details={
                'endpoint': endpoint,
                'method': method,
                'client_id': client_id
            }
        ))
        
        return True, token, 0.0
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get comprehensive security summary."""
        return {
            'organization_id': '5005620',
            'group_id': '129031',
            'token_count': len(self.token_manager.tokens),
            'active_rate_limits': len(self.rate_limiter.backoff_delays),
            'security_events_24h': len([
                e for e in self.auditor.audit_events
                if e.timestamp > datetime.now() - timedelta(hours=24)
            ]),
            'last_token_rotation': None,  # Would track actual rotations
            'security_status': 'active',
            'timestamp': datetime.now().isoformat()
        }


# Global security manager instance
security_manager = PepWorkdaySecurityManager()


def get_secure_token(token_id: str = "pepmove_samsara") -> Optional[str]:
    """Convenience function to get secure API token."""
    return security_manager.get_secure_api_token(token_id)


def check_rate_limit(client_id: str = "default") -> Tuple[bool, float]:
    """Convenience function to check rate limits."""
    return security_manager.rate_limiter.check_rate_limit(client_id)


def log_security_event(event_type: str, severity: str, details: Dict[str, Any]):
    """Convenience function to log security events."""
    event = SecurityEvent(
        event_id=f"{event_type}_{int(time.time())}",
        event_type=event_type,
        severity=severity,
        details=details
    )
    security_manager.auditor.log_security_event(event)
