"""
Advanced Rate Limiting System
Per-route rate limiting with different limits for different endpoints
"""

import time
import json
import sqlite3
from typing import Dict, Optional, Tuple
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import hashlib
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Advanced rate limiter with per-route and per-user limits"""
    
    def __init__(self, db_connection=None):
        self.db = db_connection or self._get_db_connection()
        
        # Rate limit configurations
        self.rate_limits = {
            # Authentication endpoints
            '/api/auth/login': {'requests': 5, 'window': 60, 'burst': 10},  # 5/min, burst 10
            '/api/auth/signup': {'requests': 3, 'window': 300, 'burst': 5},  # 3/5min, burst 5
            '/api/auth/reset-password': {'requests': 3, 'window': 300, 'burst': 5},
            
            # API endpoints
            '/api/planning-ai/analyze': {'requests': 10, 'window': 60, 'burst': 20},  # 10/min
            '/api/auto-docs/generate': {'requests': 5, 'window': 60, 'burst': 10},  # 5/min
            '/api/property/search': {'requests': 30, 'window': 60, 'burst': 50},  # 30/min
            
            # Marketplace endpoints
            '/api/marketplace/create-listing': {'requests': 5, 'window': 300, 'burst': 10},
            '/api/marketplace/search': {'requests': 20, 'window': 60, 'burst': 40},
            
            # Billing endpoints
            '/api/billing/webhook': {'requests': 100, 'window': 60, 'burst': 200},  # Higher for webhooks
            '/api/billing/upgrade': {'requests': 2, 'window': 300, 'burst': 3},
            
            # Admin endpoints
            '/api/admin/*': {'requests': 50, 'window': 60, 'burst': 100},
            
            # Default for unspecified endpoints
            'default': {'requests': 30, 'window': 60, 'burst': 60}  # 30/min default
        }
        
        # In-memory cache for fast lookups
        self.memory_cache = defaultdict(lambda: defaultdict(list))
        self.cache_cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def _get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect('dev.db')
        conn.row_factory = sqlite3.Row
        return conn
    
    def _get_rate_limit_config(self, endpoint: str) -> Dict:
        """Get rate limit configuration for endpoint"""
        
        # Exact match
        if endpoint in self.rate_limits:
            return self.rate_limits[endpoint]
        
        # Wildcard match
        for pattern, config in self.rate_limits.items():
            if pattern.endswith('*') and endpoint.startswith(pattern[:-1]):
                return config
        
        # Default
        return self.rate_limits['default']
    
    def _get_client_identifier(self, request_info: Dict) -> str:
        """Generate client identifier for rate limiting"""
        
        # Prefer user ID if authenticated
        if request_info.get('user_id'):
            return f"user:{request_info['user_id']}"
        
        # Fall back to IP address
        ip_address = request_info.get('ip_address', 'unknown')
        
        # Hash IP for privacy
        ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()[:16]
        return f"ip:{ip_hash}"
    
    def _cleanup_memory_cache(self):
        """Clean up expired entries from memory cache"""
        
        if time.time() - self.last_cleanup < self.cache_cleanup_interval:
            return
        
        current_time = time.time()
        
        for client_id in list(self.memory_cache.keys()):
            for endpoint in list(self.memory_cache[client_id].keys()):
                # Remove entries older than 1 hour
                self.memory_cache[client_id][endpoint] = [
                    timestamp for timestamp in self.memory_cache[client_id][endpoint]
                    if current_time - timestamp < 3600
                ]
                
                # Remove empty endpoint entries
                if not self.memory_cache[client_id][endpoint]:
                    del self.memory_cache[client_id][endpoint]
            
            # Remove empty client entries
            if not self.memory_cache[client_id]:
                del self.memory_cache[client_id]
        
        self.last_cleanup = current_time
        logger.debug("Rate limiter memory cache cleaned up")
    
    def check_rate_limit(self, endpoint: str, request_info: Dict) -> Dict:
        """Check if request is within rate limits"""
        
        self._cleanup_memory_cache()
        
        client_id = self._get_client_identifier(request_info)
        config = self._get_rate_limit_config(endpoint)
        current_time = time.time()
        
        # Get request timestamps for this client/endpoint
        request_times = self.memory_cache[client_id][endpoint]
        
        # Remove expired requests (outside window)
        window_start = current_time - config['window']
        valid_requests = [t for t in request_times if t > window_start]
        
        # Check rate limit
        if len(valid_requests) >= config['requests']:
            # Check burst limit
            burst_window_start = current_time - 10  # 10 second burst window
            recent_requests = [t for t in valid_requests if t > burst_window_start]
            
            if len(recent_requests) >= config['burst']:
                # Rate limited
                oldest_request = min(valid_requests)
                reset_time = oldest_request + config['window']
                
                # Log rate limit violation
                self._log_rate_limit_violation(client_id, endpoint, request_info)
                
                return {
                    'allowed': False,
                    'error': 'Rate limit exceeded',
                    'limit': config['requests'],
                    'window': config['window'],
                    'current_requests': len(valid_requests),
                    'reset_at': reset_time,
                    'retry_after': int(reset_time - current_time)
                }
        
        # Request allowed - record it
        valid_requests.append(current_time)
        self.memory_cache[client_id][endpoint] = valid_requests
        
        # Store in database for persistence
        self._store_request_log(client_id, endpoint, request_info)
        
        return {
            'allowed': True,
            'limit': config['requests'],
            'window': config['window'],
            'current_requests': len(valid_requests),
            'remaining': config['requests'] - len(valid_requests)
        }
    
    def _log_rate_limit_violation(self, client_id: str, endpoint: str, request_info: Dict):
        """Log rate limit violation"""
        
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO rate_limit_violations
            (client_id, endpoint, ip_address, user_agent, user_id, 
             violation_timestamp, request_info)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            client_id,
            endpoint,
            request_info.get('ip_address'),
            request_info.get('user_agent'),
            request_info.get('user_id'),
            datetime.now(timezone.utc).isoformat(),
            json.dumps(request_info)
        ))
        
        self.db.commit()
        
        logger.warning(f"Rate limit violation: {client_id} on {endpoint}")
    
    def _store_request_log(self, client_id: str, endpoint: str, request_info: Dict):
        """Store request log for analytics"""
        
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO rate_limit_requests
            (client_id, endpoint, ip_address, user_agent, user_id, 
             request_timestamp, request_info)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            client_id,
            endpoint,
            request_info.get('ip_address'),
            request_info.get('user_agent'),
            request_info.get('user_id'),
            datetime.now(timezone.utc).isoformat(),
            json.dumps(request_info)
        ))
        
        self.db.commit()
    
    def get_client_status(self, request_info: Dict) -> Dict:
        """Get current rate limit status for client"""
        
        client_id = self._get_client_identifier(request_info)
        current_time = time.time()
        
        status = {}
        
        for endpoint in self.rate_limits.keys():
            if endpoint == 'default':
                continue
                
            config = self.rate_limits[endpoint]
            request_times = self.memory_cache[client_id][endpoint]
            
            # Count valid requests
            window_start = current_time - config['window']
            valid_requests = [t for t in request_times if t > window_start]
            
            status[endpoint] = {
                'limit': config['requests'],
                'window': config['window'],
                'current_requests': len(valid_requests),
                'remaining': max(0, config['requests'] - len(valid_requests)),
                'reset_at': min(valid_requests) + config['window'] if valid_requests else current_time
            }
        
        return status
    
    def get_rate_limit_stats(self, days: int = 7) -> Dict:
        """Get rate limiting statistics"""
        
        cursor = self.db.cursor()
        since_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # Total requests and violations
        cursor.execute("""
            SELECT COUNT(*) as total_requests
            FROM rate_limit_requests
            WHERE request_timestamp > ?
        """, (since_date,))
        
        total_requests = cursor.fetchone()['total_requests']
        
        cursor.execute("""
            SELECT COUNT(*) as total_violations
            FROM rate_limit_violations
            WHERE violation_timestamp > ?
        """, (since_date,))
        
        total_violations = cursor.fetchone()['total_violations']
        
        # By endpoint
        cursor.execute("""
            SELECT endpoint, COUNT(*) as request_count
            FROM rate_limit_requests
            WHERE request_timestamp > ?
            GROUP BY endpoint
            ORDER BY request_count DESC
            LIMIT 10
        """, (since_date,))
        
        by_endpoint = cursor.fetchall()
        
        # Top violators
        cursor.execute("""
            SELECT client_id, COUNT(*) as violation_count
            FROM rate_limit_violations
            WHERE violation_timestamp > ?
            GROUP BY client_id
            ORDER BY violation_count DESC
            LIMIT 10
        """, (since_date,))
        
        top_violators = cursor.fetchall()
        
        return {
            'period_days': days,
            'total_requests': total_requests,
            'total_violations': total_violations,
            'violation_rate': round(total_violations / max(total_requests, 1) * 100, 2),
            'by_endpoint': [
                {
                    'endpoint': row['endpoint'],
                    'request_count': row['request_count']
                }
                for row in by_endpoint
            ],
            'top_violators': [
                {
                    'client_id': row['client_id'],
                    'violation_count': row['violation_count']
                }
                for row in top_violators
            ]
        }
    
    def whitelist_client(self, client_id: str, duration_hours: int = 24):
        """Temporarily whitelist a client from rate limiting"""
        
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO rate_limit_whitelist
            (client_id, whitelisted_at, expires_at, active)
            VALUES (?, ?, ?, ?)
        """, (
            client_id,
            datetime.now(timezone.utc).isoformat(),
            (datetime.now(timezone.utc) + timedelta(hours=duration_hours)).isoformat(),
            True
        ))
        
        self.db.commit()
        logger.info(f"Client {client_id} whitelisted for {duration_hours} hours")
    
    def is_client_whitelisted(self, client_id: str) -> bool:
        """Check if client is whitelisted"""
        
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT expires_at FROM rate_limit_whitelist
            WHERE client_id = ? AND active = 1
        """, (client_id,))
        
        result = cursor.fetchone()
        if not result:
            return False
        
        expires_at = datetime.fromisoformat(result['expires_at'].replace('Z', '+00:00'))
        if datetime.now(timezone.utc) > expires_at:
            # Expired - deactivate
            cursor.execute("""
                UPDATE rate_limit_whitelist
                SET active = 0
                WHERE client_id = ?
            """, (client_id,))
            self.db.commit()
            return False
        
        return True

# Rate limiting decorator
def rate_limit(endpoint: str = None, rate_limiter: RateLimiter = None):
    """Decorator for rate limiting routes"""
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract request info
            request = kwargs.get('request') or (args[0] if args else None)
            
            if not request or not rate_limiter:
                return func(*args, **kwargs)
            
            # Determine endpoint
            route_endpoint = endpoint or request.url.path
            
            # Extract request info
            request_info = {
                'ip_address': getattr(request.client, 'host', 'unknown') if hasattr(request, 'client') else 'unknown',
                'user_agent': request.headers.get('User-Agent', ''),
                'user_id': getattr(request.state, 'user_id', None) if hasattr(request, 'state') else None
            }
            
            # Check rate limit
            result = rate_limiter.check_rate_limit(route_endpoint, request_info)
            
            if not result['allowed']:
                return {
                    'error': result['error'],
                    'rate_limit': {
                        'limit': result['limit'],
                        'window': result['window'],
                        'retry_after': result['retry_after']
                    }
                }
            
            # Add rate limit headers to response
            response = func(*args, **kwargs)
            
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(result['limit'])
                response.headers['X-RateLimit-Remaining'] = str(result['remaining'])
                response.headers['X-RateLimit-Window'] = str(result['window'])
            
            return response
        
        return wrapper
    return decorator