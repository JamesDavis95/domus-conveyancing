"""
Log Redaction System
Automatically redacts PII and secrets from logs for privacy and security
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any
import hashlib

class LogRedactor:
    """Log redaction system for PII and sensitive data"""
    
    def __init__(self):
        # PII patterns
        self.pii_patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone_uk': re.compile(r'\b(?:0044|\+44|0)\d{10}\b'),
            'postcode_uk': re.compile(r'\b[A-Z]{1,2}[0-9R][0-9A-Z]?\s?[0-9][A-Z]{2}\b'),
            'national_insurance': re.compile(r'\b[A-CEGHJ-PR-TW-Z][A-CEGHJ-NPR-TW-Z]\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b'),
            'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
            'sort_code': re.compile(r'\b\d{2}[-\s]?\d{2}[-\s]?\d{2}\b'),
            'account_number': re.compile(r'\b\d{8}\b'),
            'ip_address': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            'passport': re.compile(r'\b[0-9]{9}\b'),
            'driving_licence': re.compile(r'\b[A-Z]{2}\d{6}[A-Z0-9]{3}[A-Z]{2}\b')
        }
        
        # Secret patterns
        self.secret_patterns = {
            'api_key': re.compile(r'\b(?:api[_-]?key|apikey)["\']?\s*[:=]\s*["\']?([A-Za-z0-9_-]{20,})["\']?', re.IGNORECASE),
            'jwt_token': re.compile(r'\b[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b'),
            'password': re.compile(r'\b(?:password|passwd|pwd)["\']?\s*[:=]\s*["\']?([^\s"\']{6,})["\']?', re.IGNORECASE),
            'secret_key': re.compile(r'\b(?:secret[_-]?key|secretkey)["\']?\s*[:=]\s*["\']?([A-Za-z0-9_-]{20,})["\']?', re.IGNORECASE),
            'access_token': re.compile(r'\b(?:access[_-]?token|accesstoken)["\']?\s*[:=]\s*["\']?([A-Za-z0-9_-]{20,})["\']?', re.IGNORECASE),
            'stripe_key': re.compile(r'\b(sk|pk)_(test|live)_[A-Za-z0-9]{24,}\b'),
            'aws_key': re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
            'database_url': re.compile(r'\b(?:postgres|mysql|mongodb)://[^\s]+\b', re.IGNORECASE)
        }
        
        # Sensitive field names
        self.sensitive_fields = {
            'password', 'passwd', 'pwd', 'secret', 'token', 'key', 'auth',
            'authorization', 'api_key', 'apikey', 'access_token', 'refresh_token',
            'session_id', 'csrf_token', 'credit_card', 'card_number', 'cvv',
            'sort_code', 'account_number', 'national_insurance', 'passport',
            'driving_licence', 'date_of_birth', 'dob', 'ssn', 'tin'
        }
    
    def redact_text(self, text: str) -> str:
        """Redact PII and secrets from text"""
        
        if not isinstance(text, str):
            return text
        
        redacted_text = text
        
        # Redact PII patterns
        for pattern_name, pattern in self.pii_patterns.items():
            if pattern_name == 'email':
                # Preserve domain for debugging
                redacted_text = pattern.sub(
                    lambda m: f"***@{m.group().split('@')[1]}",
                    redacted_text
                )
            elif pattern_name == 'ip_address':
                # Preserve first octet
                redacted_text = pattern.sub(
                    lambda m: f"{m.group().split('.')[0]}.***.***.***",
                    redacted_text
                )
            else:
                redacted_text = pattern.sub('[REDACTED_PII]', redacted_text)
        
        # Redact secrets
        for pattern_name, pattern in self.secret_patterns.items():
            if pattern.groups > 0:
                # Pattern has capture groups - redact only the captured part
                redacted_text = pattern.sub(
                    lambda m: m.group().replace(m.group(1), '[REDACTED_SECRET]'),
                    redacted_text
                )
            else:
                redacted_text = pattern.sub('[REDACTED_SECRET]', redacted_text)
        
        return redacted_text
    
    def redact_dict(self, data: Dict) -> Dict:
        """Redact sensitive data from dictionary"""
        
        if not isinstance(data, dict):
            return data
        
        redacted_data = {}
        
        for key, value in data.items():
            key_lower = key.lower()
            
            # Check if field name is sensitive
            if any(sensitive in key_lower for sensitive in self.sensitive_fields):
                if isinstance(value, str) and len(value) > 0:
                    # Partially redact - show first few characters
                    if len(value) <= 4:
                        redacted_data[key] = '[REDACTED]'
                    else:
                        redacted_data[key] = value[:2] + '*' * (len(value) - 4) + value[-2:]
                else:
                    redacted_data[key] = '[REDACTED]'
            elif isinstance(value, dict):
                redacted_data[key] = self.redact_dict(value)
            elif isinstance(value, list):
                redacted_data[key] = [
                    self.redact_dict(item) if isinstance(item, dict) else self.redact_text(str(item))
                    for item in value
                ]
            elif isinstance(value, str):
                redacted_data[key] = self.redact_text(value)
            else:
                redacted_data[key] = value
        
        return redacted_data
    
    def redact_json(self, json_str: str) -> str:
        """Redact sensitive data from JSON string"""
        
        try:
            data = json.loads(json_str)
            redacted_data = self.redact_dict(data)
            return json.dumps(redacted_data)
        except (json.JSONDecodeError, TypeError):
            # Fall back to text redaction
            return self.redact_text(json_str)
    
    def hash_sensitive_data(self, data: str) -> str:
        """Hash sensitive data for correlation while maintaining privacy"""
        
        if not data:
            return '[EMPTY]'
        
        # Use SHA-256 with truncation for readability
        hash_obj = hashlib.sha256(data.encode())
        return f"[HASH:{hash_obj.hexdigest()[:8]}]"
    
    def create_redacted_logger(self, logger_name: str) -> logging.Logger:
        """Create logger with automatic redaction"""
        
        logger = logging.getLogger(logger_name)
        
        # Add custom handler with redaction
        handler = RedactingHandler()
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
        
        logger.addHandler(handler)
        return logger

class RedactingHandler(logging.Handler):
    """Logging handler that automatically redacts sensitive information"""
    
    def __init__(self):
        super().__init__()
        self.redactor = LogRedactor()
    
    def emit(self, record):
        """Emit log record with redaction"""
        
        # Redact the message
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = self.redactor.redact_text(record.msg)
        
        # Redact any arguments
        if hasattr(record, 'args') and record.args:
            redacted_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    redacted_args.append(self.redactor.redact_text(arg))
                elif isinstance(arg, dict):
                    redacted_args.append(self.redactor.redact_dict(arg))
                else:
                    redacted_args.append(arg)
            record.args = tuple(redacted_args)
        
        # Call the original handler (console, file, etc.)
        if hasattr(logging.StreamHandler, 'emit'):
            logging.StreamHandler.emit(self, record)

class SecurityEventLogger:
    """Specialized logger for security events"""
    
    def __init__(self):
        self.redactor = LogRedactor()
        self.logger = logging.getLogger('security_events')
        
        # Configure security logger
        if not self.logger.handlers:
            handler = logging.FileHandler('security_events.log')
            handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
                )
            )
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_login_attempt(self, user_id: str, ip_address: str, success: bool, method: str = 'password'):
        """Log authentication attempt"""
        
        hashed_ip = self.redactor.hash_sensitive_data(ip_address)
        
        self.logger.info(
            f"Login attempt: user_id={user_id}, ip={hashed_ip}, "
            f"success={success}, method={method}"
        )
    
    def log_2fa_event(self, user_id: str, event: str, success: bool):
        """Log 2FA events"""
        
        self.logger.info(
            f"2FA event: user_id={user_id}, event={event}, success={success}"
        )
    
    def log_rate_limit_violation(self, client_id: str, endpoint: str, request_count: int):
        """Log rate limit violations"""
        
        self.logger.warning(
            f"Rate limit violation: client={client_id}, endpoint={endpoint}, "
            f"requests={request_count}"
        )
    
    def log_csp_violation(self, violation: Dict):
        """Log CSP violations"""
        
        redacted_violation = self.redactor.redact_dict(violation)
        
        self.logger.warning(
            f"CSP violation: {json.dumps(redacted_violation)}"
        )
    
    def log_admin_action(self, admin_user_id: str, action: str, target: str):
        """Log administrative actions"""
        
        self.logger.info(
            f"Admin action: admin={admin_user_id}, action={action}, target={target}"
        )
    
    def log_permission_denied(self, user_id: str, resource: str, action: str):
        """Log permission denied events"""
        
        self.logger.warning(
            f"Permission denied: user_id={user_id}, resource={resource}, action={action}"
        )
    
    def log_data_access(self, user_id: str, resource_type: str, resource_id: str, action: str):
        """Log data access events"""
        
        self.logger.info(
            f"Data access: user_id={user_id}, type={resource_type}, "
            f"id={resource_id}, action={action}"
        )

# Utility function for quick redaction
def redact_sensitive_data(data: Any) -> Any:
    """Utility function to redact sensitive data"""
    
    redactor = LogRedactor()
    
    if isinstance(data, str):
        return redactor.redact_text(data)
    elif isinstance(data, dict):
        return redactor.redact_dict(data)
    else:
        return data

# Security logger instance
security_logger = SecurityEventLogger()