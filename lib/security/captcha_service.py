"""
CAPTCHA Service for Bot Protection
Protects signup, invites, and sensitive operations from automated abuse
"""

import hashlib
import secrets
import sqlite3
import time
from typing import Dict, Optional
from datetime import datetime, timezone, timedelta
import logging
import json

logger = logging.getLogger(__name__)

class CaptchaService:
    """CAPTCHA service for bot protection"""
    
    def __init__(self, db_connection=None):
        self.db = db_connection or self._get_db_connection()
        self.challenge_expiry = 300  # 5 minutes
        self.max_attempts = 3
    
    def _get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect('dev.db')
        conn.row_factory = sqlite3.Row
        return conn
    
    def generate_math_challenge(self) -> Dict:
        """Generate a simple math CAPTCHA challenge"""
        
        # Generate two random numbers
        num1 = secrets.randbelow(50) + 1
        num2 = secrets.randbelow(50) + 1
        
        # Random operation
        operations = ['+', '-', '*']
        operation = secrets.choice(operations)
        
        if operation == '+':
            answer = num1 + num2
            question = f"What is {num1} + {num2}?"
        elif operation == '-':
            # Ensure positive result
            if num1 < num2:
                num1, num2 = num2, num1
            answer = num1 - num2
            question = f"What is {num1} - {num2}?"
        else:  # multiplication
            # Keep numbers small for multiplication
            num1 = secrets.randbelow(12) + 1
            num2 = secrets.randbelow(12) + 1
            answer = num1 * num2
            question = f"What is {num1} × {num2}?"
        
        # Generate challenge ID
        challenge_id = secrets.token_urlsafe(16)
        
        # Store challenge
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO captcha_challenges
            (challenge_id, challenge_type, question, answer_hash, 
             created_at, expires_at, attempts)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            challenge_id,
            'math',
            question,
            hashlib.sha256(str(answer).encode()).hexdigest(),
            datetime.now(timezone.utc).isoformat(),
            (datetime.now(timezone.utc) + timedelta(seconds=self.challenge_expiry)).isoformat(),
            0
        ))
        
        self.db.commit()
        
        return {
            'challenge_id': challenge_id,
            'question': question,
            'type': 'math',
            'expires_in': self.challenge_expiry
        }
    
    def generate_text_challenge(self) -> Dict:
        """Generate a text-based CAPTCHA challenge"""
        
        # Simple text challenges
        challenges = [
            {"question": "What comes after 'A, B, C'?", "answer": "D"},
            {"question": "What is the first day of the week?", "answer": "Monday"},
            {"question": "How many sides does a triangle have?", "answer": "3"},
            {"question": "What color do you get from mixing red and white?", "answer": "Pink"},
            {"question": "What is the opposite of 'hot'?", "answer": "Cold"},
            {"question": "Complete: 'The sky is ___'", "answer": "Blue"},
            {"question": "What is 2 + 2?", "answer": "4"},
            {"question": "What animal says 'meow'?", "answer": "Cat"},
            {"question": "How many hours are in a day?", "answer": "24"},
            {"question": "What is the capital of the UK?", "answer": "London"}
        ]
        
        challenge = secrets.choice(challenges)
        challenge_id = secrets.token_urlsafe(16)
        
        # Store challenge
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO captcha_challenges
            (challenge_id, challenge_type, question, answer_hash,
             created_at, expires_at, attempts)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            challenge_id,
            'text',
            challenge['question'],
            hashlib.sha256(challenge['answer'].lower().encode()).hexdigest(),
            datetime.now(timezone.utc).isoformat(),
            (datetime.now(timezone.utc) + timedelta(seconds=self.challenge_expiry)).isoformat(),
            0
        ))
        
        self.db.commit()
        
        return {
            'challenge_id': challenge_id,
            'question': challenge['question'],
            'type': 'text',
            'expires_in': self.challenge_expiry
        }
    
    def verify_challenge(self, challenge_id: str, answer: str, ip_address: str = None) -> Dict:
        """Verify CAPTCHA challenge answer"""
        
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT challenge_type, answer_hash, expires_at, attempts, solved
            FROM captcha_challenges
            WHERE challenge_id = ?
        """, (challenge_id,))
        
        result = cursor.fetchone()
        if not result:
            return {
                'success': False,
                'error': 'Invalid challenge ID',
                'remaining_attempts': 0
            }
        
        # Check if already solved
        if result['solved']:
            return {
                'success': False,
                'error': 'Challenge already used',
                'remaining_attempts': 0
            }
        
        # Check expiry
        expires_at = datetime.fromisoformat(result['expires_at'].replace('Z', '+00:00'))
        if datetime.now(timezone.utc) > expires_at:
            return {
                'success': False,
                'error': 'Challenge expired',
                'remaining_attempts': 0
            }
        
        # Check attempt limit
        attempts = result['attempts']
        if attempts >= self.max_attempts:
            return {
                'success': False,
                'error': 'Too many attempts',
                'remaining_attempts': 0
            }
        
        # Verify answer
        answer_hash = hashlib.sha256(answer.lower().strip().encode()).hexdigest()
        is_correct = answer_hash == result['answer_hash']
        
        # Update attempts
        new_attempts = attempts + 1
        
        if is_correct:
            # Mark as solved
            cursor.execute("""
                UPDATE captcha_challenges
                SET attempts = ?, solved = 1, solved_at = ?, solver_ip = ?
                WHERE challenge_id = ?
            """, (
                new_attempts,
                datetime.now(timezone.utc).isoformat(),
                ip_address,
                challenge_id
            ))
            
            self.db.commit()
            
            return {
                'success': True,
                'verified': True,
                'challenge_id': challenge_id
            }
        else:
            # Increment attempts
            cursor.execute("""
                UPDATE captcha_challenges
                SET attempts = ?
                WHERE challenge_id = ?
            """, (new_attempts, challenge_id))
            
            self.db.commit()
            
            remaining = self.max_attempts - new_attempts
            return {
                'success': False,
                'error': 'Incorrect answer',
                'remaining_attempts': remaining
            }
    
    def is_challenge_solved(self, challenge_id: str) -> bool:
        """Check if challenge has been solved"""
        
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT solved FROM captcha_challenges
            WHERE challenge_id = ? AND solved = 1
        """, (challenge_id,))
        
        return cursor.fetchone() is not None
    
    def cleanup_expired_challenges(self) -> int:
        """Clean up expired challenges"""
        
        cursor = self.db.cursor()
        cursor.execute("""
            DELETE FROM captcha_challenges
            WHERE expires_at < ?
        """, (datetime.now(timezone.utc).isoformat(),))
        
        deleted_count = cursor.rowcount
        self.db.commit()
        
        logger.info(f"Cleaned up {deleted_count} expired CAPTCHA challenges")
        return deleted_count
    
    def get_challenge_stats(self, days: int = 7) -> Dict:
        """Get CAPTCHA challenge statistics"""
        
        cursor = self.db.cursor()
        since_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # Total challenges created
        cursor.execute("""
            SELECT COUNT(*) as total_challenges,
                   SUM(CASE WHEN solved = 1 THEN 1 ELSE 0 END) as solved_challenges,
                   AVG(attempts) as avg_attempts
            FROM captcha_challenges
            WHERE created_at > ?
        """, (since_date,))
        
        stats = cursor.fetchone()
        
        # By challenge type
        cursor.execute("""
            SELECT challenge_type, COUNT(*) as count,
                   SUM(CASE WHEN solved = 1 THEN 1 ELSE 0 END) as solved
            FROM captcha_challenges
            WHERE created_at > ?
            GROUP BY challenge_type
        """, (since_date,))
        
        by_type = cursor.fetchall()
        
        return {
            'period_days': days,
            'total_challenges': stats['total_challenges'] or 0,
            'solved_challenges': stats['solved_challenges'] or 0,
            'success_rate': round((stats['solved_challenges'] or 0) / max(stats['total_challenges'] or 1, 1) * 100, 1),
            'average_attempts': round(stats['avg_attempts'] or 0, 1),
            'by_type': [
                {
                    'type': row['challenge_type'],
                    'total': row['count'],
                    'solved': row['solved'],
                    'success_rate': round(row['solved'] / max(row['count'], 1) * 100, 1)
                }
                for row in by_type
            ]
        }

class CaptchaMiddleware:
    """Middleware to enforce CAPTCHA on specific endpoints"""
    
    def __init__(self, captcha_service: CaptchaService):
        self.captcha_service = captcha_service
        
        # Endpoints that require CAPTCHA
        self.protected_endpoints = {
            '/api/auth/signup',
            '/api/auth/invite',
            '/api/auth/reset-password',
            '/api/billing/upgrade',
            '/api/marketplace/create-listing'
        }
    
    def require_captcha(self, request_path: str) -> bool:
        """Check if endpoint requires CAPTCHA"""
        return request_path in self.protected_endpoints
    
    def validate_captcha_header(self, headers: Dict) -> Dict:
        """Validate CAPTCHA from request headers"""
        
        challenge_id = headers.get('X-Captcha-Challenge')
        answer = headers.get('X-Captcha-Answer')
        
        if not challenge_id or not answer:
            return {
                'valid': False,
                'error': 'Missing CAPTCHA challenge or answer'
            }
        
        # Verify challenge
        result = self.captcha_service.verify_challenge(
            challenge_id, 
            answer,
            headers.get('X-Forwarded-For', headers.get('X-Real-IP'))
        )
        
        return {
            'valid': result.get('success', False),
            'error': result.get('error'),
            'remaining_attempts': result.get('remaining_attempts', 0)
        }

# CAPTCHA decorator for route protection
def require_captcha(captcha_service: CaptchaService):
    """Decorator to require CAPTCHA verification on routes"""
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract request from FastAPI dependency injection
            request = kwargs.get('request') or (args[0] if args else None)
            
            if not request:
                return {'error': 'Request context not available'}
            
            # Check CAPTCHA headers
            challenge_id = request.headers.get('X-Captcha-Challenge')
            answer = request.headers.get('X-Captcha-Answer')
            
            if not challenge_id or not answer:
                return {
                    'error': 'CAPTCHA verification required',
                    'captcha_required': True
                }
            
            # Verify CAPTCHA
            result = captcha_service.verify_challenge(
                challenge_id, 
                answer,
                request.client.host if hasattr(request, 'client') else None
            )
            
            if not result.get('success'):
                return {
                    'error': result.get('error', 'CAPTCHA verification failed'),
                    'captcha_required': True,
                    'remaining_attempts': result.get('remaining_attempts', 0)
                }
            
            # CAPTCHA verified, proceed with original function
            return func(*args, **kwargs)
        
        return wrapper
    return decorator