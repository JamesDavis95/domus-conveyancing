"""
Two-Factor Authentication (2FA) System
Mandatory 2FA for admin users with TOTP and backup codes
"""

try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    qrcode = None

try:
    import pyotp
    PYOTP_AVAILABLE = True
except ImportError:
    PYOTP_AVAILABLE = False
    pyotp = None

import secrets
import hashlib
import sqlite3
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from io import BytesIO
import base64
import logging

logger = logging.getLogger(__name__)

class TwoFactorAuth:
    """Two-Factor Authentication manager with TOTP and backup codes"""
    
    def __init__(self, db_connection=None):
        self.db = db_connection or self._get_db_connection()
        self.app_name = "Domus Planning Platform"
        self.issuer = "domus.conveyancing"
    
    def _get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect('dev.db')
        conn.row_factory = sqlite3.Row
        return conn
    
    def generate_secret_key(self) -> str:
        """Generate a new TOTP secret key"""
        if not PYOTP_AVAILABLE:
            raise ImportError("pyotp package required for 2FA functionality")
        return pyotp.random_base32()
    
    def generate_backup_codes(self, count: int = 8) -> List[str]:
        """Generate backup codes for 2FA recovery"""
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric codes
            code = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
            codes.append(f"{code[:4]}-{code[4:]}")
        return codes
    
    def hash_backup_code(self, code: str) -> str:
        """Hash backup code for secure storage"""
        # Remove hyphens and convert to uppercase
        clean_code = code.replace('-', '').upper()
        return hashlib.sha256(clean_code.encode()).hexdigest()
    
    def setup_2fa_for_user(self, user_id: str, email: str) -> Dict:
        """Set up 2FA for a user"""
        
        # Generate secret key
        secret_key = self.generate_secret_key()
        
        # Generate backup codes
        backup_codes = self.generate_backup_codes()
        hashed_codes = [self.hash_backup_code(code) for code in backup_codes]
        
        # Create TOTP instance
        if not PYOTP_AVAILABLE:
            raise ImportError("pyotp package required for 2FA functionality")
        totp = pyotp.TOTP(secret_key)
        
        # Generate QR code
        provisioning_uri = totp.provisioning_uri(
            name=email,
            issuer_name=self.issuer
        )
        
        qr_base64 = None
        if QRCODE_AVAILABLE:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert QR code to base64 for web display
            buffer = BytesIO()
            qr_img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        else:
            # QR code not available, user will need to enter secret manually
            pass
        
        # Store in database (not yet enabled)
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO user_2fa_setup
            (user_id, secret_key, backup_codes_hash, setup_timestamp, enabled)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            secret_key,
            ','.join(hashed_codes),
            datetime.now(timezone.utc).isoformat(),
            False  # Not enabled until verification
        ))
        
        self.db.commit()
        
        return {
            'secret_key': secret_key,
            'qr_code_data': qr_base64,
            'provisioning_uri': provisioning_uri,
            'backup_codes': backup_codes,
            'manual_entry_key': secret_key
        }
    
    def verify_setup_token(self, user_id: str, token: str) -> bool:
        """Verify setup token and enable 2FA"""
        
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT secret_key FROM user_2fa_setup
            WHERE user_id = ? AND enabled = 0
        """, (user_id,))
        
        result = cursor.fetchone()
        if not result:
            return False
        
        secret_key = result['secret_key']
        
        if not PYOTP_AVAILABLE:
            raise ImportError("pyotp package required for 2FA functionality")
        totp = pyotp.TOTP(secret_key)
        
        # Verify token with 30-second window tolerance
        if totp.verify(token, valid_window=1):
            # Enable 2FA
            cursor.execute("""
                UPDATE user_2fa_setup
                SET enabled = 1, enabled_timestamp = ?
                WHERE user_id = ?
            """, (datetime.now(timezone.utc).isoformat(), user_id))
            
            # Update user record
            cursor.execute("""
                UPDATE users
                SET two_factor_enabled = 1, two_factor_enabled_at = ?
                WHERE id = ?
            """, (datetime.now(timezone.utc).isoformat(), user_id))
            
            self.db.commit()
            logger.info(f"2FA enabled for user {user_id}")
            return True
        
        return False
    
    def verify_totp_token(self, user_id: str, token: str) -> bool:
        """Verify TOTP token for authentication"""
        
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT secret_key FROM user_2fa_setup
            WHERE user_id = ? AND enabled = 1
        """, (user_id,))
        
        result = cursor.fetchone()
        if not result:
            return False
        
        secret_key = result['secret_key']
        totp = pyotp.TOTP(secret_key)
        
        # Verify with 30-second window tolerance
        is_valid = totp.verify(token, valid_window=1)
        
        if is_valid:
            # Log successful verification
            cursor.execute("""
                INSERT INTO user_2fa_verifications
                (user_id, verification_type, verified_at, success)
                VALUES (?, ?, ?, ?)
            """, (user_id, 'totp', datetime.now(timezone.utc).isoformat(), True))
            self.db.commit()
        
        return is_valid
    
    def verify_backup_code(self, user_id: str, code: str) -> bool:
        """Verify and consume a backup code"""
        
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT backup_codes_hash, used_backup_codes FROM user_2fa_setup
            WHERE user_id = ? AND enabled = 1
        """, (user_id,))
        
        result = cursor.fetchone()
        if not result:
            return False
        
        backup_codes_hash = result['backup_codes_hash']
        used_codes = result['used_backup_codes'] or ''
        
        # Hash the provided code
        code_hash = self.hash_backup_code(code)
        
        # Check if code exists and hasn't been used
        if code_hash in backup_codes_hash and code_hash not in used_codes:
            # Mark code as used
            used_codes_list = used_codes.split(',') if used_codes else []
            used_codes_list.append(code_hash)
            new_used_codes = ','.join(used_codes_list)
            
            cursor.execute("""
                UPDATE user_2fa_setup
                SET used_backup_codes = ?
                WHERE user_id = ?
            """, (new_used_codes, user_id))
            
            # Log successful verification
            cursor.execute("""
                INSERT INTO user_2fa_verifications
                (user_id, verification_type, verified_at, success)
                VALUES (?, ?, ?, ?)
            """, (user_id, 'backup_code', datetime.now(timezone.utc).isoformat(), True))
            
            self.db.commit()
            
            logger.warning(f"Backup code used for user {user_id}")
            return True
        
        return False
    
    def is_2fa_enabled(self, user_id: str) -> bool:
        """Check if 2FA is enabled for user"""
        
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT enabled FROM user_2fa_setup
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        return result and result['enabled']
    
    def disable_2fa(self, user_id: str, admin_user_id: str = None) -> bool:
        """Disable 2FA for a user (admin action)"""
        
        cursor = self.db.cursor()
        
        # Disable in 2FA setup
        cursor.execute("""
            UPDATE user_2fa_setup
            SET enabled = 0, disabled_timestamp = ?, disabled_by = ?
            WHERE user_id = ?
        """, (datetime.now(timezone.utc).isoformat(), admin_user_id, user_id))
        
        # Update user record
        cursor.execute("""
            UPDATE users
            SET two_factor_enabled = 0, two_factor_disabled_at = ?
            WHERE id = ?
        """, (datetime.now(timezone.utc).isoformat(), user_id))
        
        self.db.commit()
        
        logger.warning(f"2FA disabled for user {user_id} by admin {admin_user_id}")
        return True
    
    def get_remaining_backup_codes(self, user_id: str) -> int:
        """Get count of remaining backup codes"""
        
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT backup_codes_hash, used_backup_codes FROM user_2fa_setup
            WHERE user_id = ? AND enabled = 1
        """, (user_id,))
        
        result = cursor.fetchone()
        if not result:
            return 0
        
        total_codes = len(result['backup_codes_hash'].split(','))
        used_codes = len(result['used_backup_codes'].split(',')) if result['used_backup_codes'] else 0
        
        return total_codes - used_codes
    
    def regenerate_backup_codes(self, user_id: str) -> List[str]:
        """Generate new backup codes for user"""
        
        new_codes = self.generate_backup_codes()
        hashed_codes = [self.hash_backup_code(code) for code in new_codes]
        
        cursor = self.db.cursor()
        cursor.execute("""
            UPDATE user_2fa_setup
            SET backup_codes_hash = ?, used_backup_codes = NULL,
                backup_codes_regenerated_at = ?
            WHERE user_id = ?
        """, (
            ','.join(hashed_codes),
            datetime.now(timezone.utc).isoformat(),
            user_id
        ))
        
        self.db.commit()
        
        logger.info(f"Backup codes regenerated for user {user_id}")
        return new_codes
    
    def get_2fa_status(self, user_id: str) -> Dict:
        """Get comprehensive 2FA status for user"""
        
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT enabled, setup_timestamp, enabled_timestamp,
                   backup_codes_regenerated_at
            FROM user_2fa_setup
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        if not result:
            return {'enabled': False, 'setup': False}
        
        # Get recent verifications
        cursor.execute("""
            SELECT verification_type, verified_at, success
            FROM user_2fa_verifications
            WHERE user_id = ?
            ORDER BY verified_at DESC
            LIMIT 10
        """, (user_id,))
        
        recent_verifications = cursor.fetchall()
        
        return {
            'enabled': bool(result['enabled']),
            'setup': True,
            'setup_date': result['setup_timestamp'],
            'enabled_date': result['enabled_timestamp'],
            'backup_codes_remaining': self.get_remaining_backup_codes(user_id),
            'backup_codes_regenerated': result['backup_codes_regenerated_at'],
            'recent_verifications': [
                {
                    'type': v['verification_type'],
                    'timestamp': v['verified_at'],
                    'success': bool(v['success'])
                }
                for v in recent_verifications
            ]
        }