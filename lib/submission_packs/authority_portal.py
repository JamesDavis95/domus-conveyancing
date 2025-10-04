"""
Authority Portal for Document Verification
Secure portal for planning authorities to verify submission pack integrity
"""

import sqlite3
import json
from datetime import datetime, timezone
import tempfile
import os
from typing import Dict, List, Optional
import logging

from .generator import SubmissionPackManager, SubmissionPackGenerator

logger = logging.getLogger(__name__)

# Mock authority credentials for testing (in production, use proper auth system)
AUTHORITY_CREDENTIALS = {
    'E06000001': {'username': 'brighton_hove', 'password_hash': 'hashed_secure_auth_2024'},
    'E07000223': {'username': 'adur_dc', 'password_hash': 'hashed_secure_auth_2024'},
    'E07000224': {'username': 'arun_dc', 'password_hash': 'hashed_secure_auth_2024'},
    'E07000061': {'username': 'eastbourne_bc', 'password_hash': 'hashed_secure_auth_2024'},
    'E07000062': {'username': 'hastings_bc', 'password_hash': 'hashed_secure_auth_2024'},
}

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('dev.db')
    conn.row_factory = sqlite3.Row
    return conn

def require_authority_auth(lpa_code: str, username: str, password: str) -> bool:
    """Verify authority credentials (simplified for testing)"""
    if lpa_code not in AUTHORITY_CREDENTIALS:
        return False
    
    auth_data = AUTHORITY_CREDENTIALS[lpa_code]
    # Simplified auth check for testing
    return auth_data['username'] == username and password == 'secure_auth_2024'

# Flask routes commented out for testing - would be enabled with Flask installation
# @authority_portal.route('/login')
# def login():
#     """Authority login page"""
#     return render_template('authority/login.html')

# API functions for testing and integration

def search_submissions_api(lpa_code: str = None, app_ref: str = None, status: str = 'all', limit: int = 20) -> Dict:
    """API endpoint for searching submissions"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build query
    query = "SELECT * FROM submission_packs WHERE 1=1"
    params = []
    
    if lpa_code:
        query += " AND application_reference LIKE ?"
        params.append(f"{lpa_code}%")
    
    if app_ref:
        query += " AND application_reference LIKE ?"
        params.append(f"%{app_ref}%")
    
    if status == 'verified':
        query += " AND integrity_verified = 1"
    elif status == 'unverified':
        query += " AND integrity_verified = 0"
    
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    submissions = cursor.fetchall()
    
    conn.close()
    
    # Convert to JSON-serializable format
    results = []
    for sub in submissions:
        results.append({
            'submission_id': sub['submission_id'],
            'application_reference': sub['application_reference'],
            'total_documents': sub['total_documents'],
            'total_size_mb': round(sub['total_size_bytes'] / (1024 * 1024), 2),
            'integrity_verified': bool(sub['integrity_verified']),
            'created_at': sub['created_at']
        })
    
    return {
        'success': True,
        'submissions': results,
        'total_found': len(results)
    }

# Flask route stubs commented out - would be enabled with Flask installation
# The rest of the Flask routes would go here when Flask is available

class DocumentVerificationAPI:
    """API for external document verification"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.generator = SubmissionPackGenerator()
    
    def verify_document_integrity(self, document_hash: str, submission_id: str) -> Dict:
        """Verify individual document integrity"""
        cursor = self.db.cursor()
        
        # Get submission manifest
        cursor.execute("""
            SELECT manifest_json FROM submission_packs
            WHERE submission_id = ?
        """, (submission_id,))
        
        result = cursor.fetchone()
        if not result:
            return {'verified': False, 'error': 'Submission not found'}
        
        # Handle both Row objects and tuples
        if hasattr(result, 'keys'):
            manifest_json = result['manifest_json']
        else:
            manifest_json = result[0]
        
        manifest_data = json.loads(manifest_json)
        
        # Find document in manifest
        for doc in manifest_data['documents']:
            if doc['sha256_hash'] == document_hash:
                return {
                    'verified': True,
                    'document': {
                        'filename': doc['original_name'],
                        'document_type': doc['document_type'],
                        'file_size': doc['file_size'],
                        'upload_timestamp': doc['upload_timestamp'],
                        'required': doc['required']
                    }
                }
        
        return {'verified': False, 'error': 'Document hash not found in submission'}
    
    def get_submission_summary(self, submission_id: str) -> Dict:
        """Get summary of submission pack for verification"""
        cursor = self.db.cursor()
        
        cursor.execute("""
            SELECT submission_id, application_reference, total_documents,
                   total_size_bytes, integrity_verified, created_at, manifest_json
            FROM submission_packs
            WHERE submission_id = ?
        """, (submission_id,))
        
        result = cursor.fetchone()
        if not result:
            return {'error': 'Submission not found'}
        
        # Handle both Row objects and tuples
        if hasattr(result, 'keys'):
            # Row object with column names
            manifest_data = json.loads(result['manifest_json'])
            return {
                'submission_id': result['submission_id'],
                'application_reference': result['application_reference'],
                'total_documents': result['total_documents'],
                'total_size_mb': round(result['total_size_bytes'] / (1024 * 1024), 2),
                'integrity_verified': bool(result['integrity_verified']),
                'created_at': result['created_at'],
                'documents': [
                    {
                        'filename': doc['original_name'],
                        'document_type': doc['document_type'],
                        'file_size': doc['file_size'],
                        'required': doc['required'],
                        'sha256_hash': doc['sha256_hash'][:16] + '...'  # Truncated for security
                    }
                    for doc in manifest_data['documents']
                ]
            }
        else:
            # Tuple result
            submission_id, app_ref, total_docs, total_size, verified, created_at, manifest_json = result
            manifest_data = json.loads(manifest_json)
            return {
                'submission_id': submission_id,
                'application_reference': app_ref,
                'total_documents': total_docs,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'integrity_verified': bool(verified),
                'created_at': created_at,
                'documents': [
                    {
                        'filename': doc['original_name'],
                        'document_type': doc['document_type'],
                        'file_size': doc['file_size'],
                        'required': doc['required'],
                        'sha256_hash': doc['sha256_hash'][:16] + '...'  # Truncated for security
                    }
                    for doc in manifest_data['documents']
                ]
            }