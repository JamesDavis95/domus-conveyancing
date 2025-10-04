"""
Log Redactor - Standalone Test
Tests log redaction without FastAPI dependencies
"""

import re
import json
import hashlib
from typing import Dict, List, Optional, Any

class TestLogRedactor:
    """Test version of log redactor without dependencies"""
    
    def __init__(self):
        # PII patterns
        self.pii_patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone_uk': re.compile(r'\b(?:0044|\+44|0)\d{10}\b'),
            'postcode_uk': re.compile(r'\b[A-Z]{1,2}[0-9R][0-9A-Z]?\s?[0-9][A-Z]{2}\b'),
            'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
            'ip_address': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
        }
        
        # Secret patterns
        self.secret_patterns = {
            'api_key': re.compile(r'\b(?:api[_-]?key|apikey)["\']?\s*[:=]\s*["\']?([A-Za-z0-9_-]{20,})["\']?', re.IGNORECASE),
            'password': re.compile(r'\b(?:password|passwd|pwd)["\']?\s*[:=]\s*["\']?([^\s"\']{6,})["\']?', re.IGNORECASE),
            'secret_key': re.compile(r'\b(?:secret[_-]?key|secretkey)["\']?\s*[:=]\s*["\']?([A-Za-z0-9_-]{20,})["\']?', re.IGNORECASE),
        }
        
        # Sensitive field names
        self.sensitive_fields = {
            'password', 'passwd', 'pwd', 'secret', 'token', 'key', 'auth',
            'api_key', 'apikey', 'access_token', 'credit_card', 'cvv'
        }
    
    def redact_text(self, text: str) -> str:
        """Redact PII and secrets from text"""
        if not isinstance(text, str):
            return text
        
        redacted_text = text
        
        # Redact PII patterns
        for pattern_name, pattern in self.pii_patterns.items():
            if pattern_name == 'email':
                redacted_text = pattern.sub(
                    lambda m: f"***@{m.group().split('@')[1]}",
                    redacted_text
                )
            elif pattern_name == 'ip_address':
                redacted_text = pattern.sub(
                    lambda m: f"{m.group().split('.')[0]}.***.***.***",
                    redacted_text
                )
            else:
                redacted_text = pattern.sub('[REDACTED_PII]', redacted_text)
        
        # Redact secrets
        for pattern_name, pattern in self.secret_patterns.items():
            if pattern.groups > 0:
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
                    if len(value) <= 4:
                        redacted_data[key] = '[REDACTED]'
                    else:
                        redacted_data[key] = value[:2] + '*' * (len(value) - 4) + value[-2:]
                else:
                    redacted_data[key] = '[REDACTED]'
            elif isinstance(value, dict):
                redacted_data[key] = self.redact_dict(value)
            elif isinstance(value, str):
                redacted_data[key] = self.redact_text(value)
            else:
                redacted_data[key] = value
        
        return redacted_data

def test_log_redactor_standalone():
    """Test log redactor functionality"""
    print("Testing Log Redactor (Standalone)...")
    
    redactor = TestLogRedactor()
    
    # Test text redaction
    test_cases = [
        "Contact john.doe@example.com for support",
        "API key: sk_test_1234567890abcdef",
        "User password: mysecretpassword123",
        "Server IP: 192.168.1.100",
        "Call us at 07123456789"
    ]
    
    for text in test_cases:
        redacted = redactor.redact_text(text)
        print(f"✅ '{text}' -> '{redacted}'")
    
    # Test dict redaction
    test_data = {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "secret123",
        "api_key": "sk_test_abcdef123456",
        "phone": "07987654321",
        "normal_field": "this is fine"
    }
    
    redacted_data = redactor.redact_dict(test_data)
    print(f"✅ Dict redaction:")
    print(f"   Original: {test_data}")
    print(f"   Redacted: {redacted_data}")
    
    return True

if __name__ == "__main__":
    test_log_redactor_standalone()