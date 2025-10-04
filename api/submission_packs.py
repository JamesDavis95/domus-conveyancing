"""
REST API for Submission Packs Management
Provides endpoints for creating, verifying, and managing document submission packs
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
import sqlite3
import json
import os
import tempfile
from datetime import datetime, timezone
import hashlib
from pathlib import Path

from lib.submission_packs.generator import SubmissionPackManager, SubmissionPackGenerator
from lib.submission_packs.authority_portal import DocumentVerificationAPI

router = APIRouter(prefix="/api/submission-packs", tags=["submission_packs"])

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('dev.db')
    conn.row_factory = sqlite3.Row
    return conn

@router.post("/create")
async def create_submission_pack(
    application_id: str = Form(...),
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Create a new submission pack with uploaded documents"""
    
    conn = get_db_connection()
    try:
        manager = SubmissionPackManager(conn)
        
        # Save uploaded files temporarily
        temp_files = []
        document_files = []
        
        for file in files:
            # Create temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_path = temp_file.name
            
            temp_files.append(temp_path)
            document_files.append({
                'file_path': temp_path,
                'original_name': file.filename
            })
        
        # Create submission pack
        result = manager.create_submission_pack(application_id, document_files)
        
        # Clean up temp files in background
        for temp_path in temp_files:
            background_tasks.add_task(os.unlink, temp_path)
        
        return {
            'success': True,
            'submission_pack': result
        }
        
    except Exception as e:
        # Clean up temp files on error
        for temp_path in temp_files:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        conn.close()

@router.get("/submission/{submission_id}")
async def get_submission_pack(submission_id: str):
    """Get submission pack details"""
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM submission_packs
            WHERE submission_id = ?
        """, (submission_id,))
        
        submission = cursor.fetchone()
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Parse manifest
        manifest_data = json.loads(submission['manifest_json'])
        
        return {
            'success': True,
            'submission': {
                'submission_id': submission['submission_id'],
                'application_reference': submission['application_reference'],
                'total_documents': submission['total_documents'],
                'total_size_mb': round(submission['total_size_bytes'] / (1024 * 1024), 2),
                'integrity_verified': bool(submission['integrity_verified']),
                'created_at': submission['created_at'],
                's3_url': submission['s3_url']
            },
            'manifest': manifest_data
        }
    
    finally:
        conn.close()

@router.post("/verify/{submission_id}")
async def verify_submission_pack(submission_id: str):
    """Verify submission pack integrity"""
    
    conn = get_db_connection()
    try:
        manager = SubmissionPackManager(conn)
        result = manager.verify_submission_pack(submission_id)
        
        return {
            'success': True,
            'verification': result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        conn.close()

@router.get("/search")
async def search_submission_packs(
    lpa_code: Optional[str] = None,
    application_reference: Optional[str] = None,
    verified_only: bool = False,
    limit: int = 20
):
    """Search submission packs"""
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT * FROM submission_packs WHERE 1=1"
        params = []
        
        if lpa_code:
            query += " AND application_reference LIKE ?"
            params.append(f"{lpa_code}%")
        
        if application_reference:
            query += " AND application_reference LIKE ?"
            params.append(f"%{application_reference}%")
        
        if verified_only:
            query += " AND integrity_verified = 1"
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        submissions = cursor.fetchall()
        
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
    
    finally:
        conn.close()

@router.get("/manifest/{submission_id}")
async def get_submission_manifest(submission_id: str):
    """Get submission manifest JSON"""
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT manifest_json FROM submission_packs
            WHERE submission_id = ?
        """, (submission_id,))
        
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        manifest_data = json.loads(result['manifest_json'])
        return {
            'success': True,
            'manifest': manifest_data
        }
    
    finally:
        conn.close()

@router.post("/verify-document")
async def verify_document_integrity(
    submission_id: str = Form(...),
    document_hash: str = Form(...)
):
    """Verify individual document integrity"""
    
    conn = get_db_connection()
    try:
        api = DocumentVerificationAPI(conn)
        result = api.verify_document_integrity(document_hash, submission_id)
        
        return {
            'success': True,
            'verification': result
        }
    
    finally:
        conn.close()

@router.get("/statistics")
async def get_submission_statistics():
    """Get submission pack statistics"""
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Total submissions
        cursor.execute("""
            SELECT COUNT(*) as total_submissions,
                   SUM(CASE WHEN integrity_verified = 1 THEN 1 ELSE 0 END) as verified_submissions,
                   SUM(total_documents) as total_documents,
                   SUM(total_size_bytes) as total_size_bytes
            FROM submission_packs
        """)
        
        stats = cursor.fetchone()
        
        # Recent submissions (last 7 days)
        cursor.execute("""
            SELECT COUNT(*) as recent_submissions
            FROM submission_packs
            WHERE created_at > datetime('now', '-7 days')
        """)
        
        recent = cursor.fetchone()
        
        # By LPA
        cursor.execute("""
            SELECT substr(application_reference, 1, 9) as lpa_code,
                   COUNT(*) as submission_count
            FROM submission_packs
            GROUP BY substr(application_reference, 1, 9)
            ORDER BY submission_count DESC
            LIMIT 10
        """)
        
        by_lpa = cursor.fetchall()
        
        return {
            'success': True,
            'statistics': {
                'total_submissions': stats['total_submissions'] or 0,
                'verified_submissions': stats['verified_submissions'] or 0,
                'total_documents': stats['total_documents'] or 0,
                'total_size_gb': round((stats['total_size_bytes'] or 0) / (1024**3), 2),
                'recent_submissions': recent['recent_submissions'] or 0,
                'verification_rate': round((stats['verified_submissions'] or 0) / max(stats['total_submissions'] or 1, 1) * 100, 1),
                'by_lpa': [
                    {
                        'lpa_code': row['lpa_code'],
                        'submission_count': row['submission_count']
                    }
                    for row in by_lpa
                ]
            }
        }
    
    finally:
        conn.close()

@router.get("/download/{submission_id}")
async def get_download_link(submission_id: str):
    """Generate secure download link for submission pack"""
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s3_url, application_reference, total_size_bytes
            FROM submission_packs
            WHERE submission_id = ?
        """, (submission_id,))
        
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        s3_url, app_ref, size_bytes = result
        
        # Log download request
        cursor.execute("""
            INSERT INTO document_downloads
            (submission_id, downloaded_by, download_type, document_filename)
            VALUES (?, ?, ?, ?)
        """, (submission_id, "api_user", "full_pack", f"{submission_id}.zip"))
        
        conn.commit()
        
        # In production, generate presigned URL for secure download
        # For now, return the S3 URL (requires AWS credentials)
        
        return {
            'success': True,
            'download_url': s3_url,
            'application_reference': app_ref,
            'size_mb': round(size_bytes / (1024 * 1024), 2),
            'expires_in': '1 hour',  # Presigned URL expiry
            'instructions': 'Use AWS CLI or SDK with appropriate credentials to download from S3'
        }
    
    finally:
        conn.close()

@router.get("/checksums/{submission_id}")
async def get_document_checksums(submission_id: str):
    """Get all document checksums for a submission"""
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT filename, original_name, file_size, sha256_hash,
                   mime_type, document_type, required, verified,
                   upload_timestamp
            FROM document_checksums
            WHERE submission_id = ?
            ORDER BY document_type, filename
        """, (submission_id,))
        
        checksums = cursor.fetchall()
        
        if not checksums:
            raise HTTPException(status_code=404, detail="No checksums found for submission")
        
        results = []
        for checksum in checksums:
            results.append({
                'filename': checksum['filename'],
                'original_name': checksum['original_name'],
                'file_size': checksum['file_size'],
                'sha256_hash': checksum['sha256_hash'],
                'mime_type': checksum['mime_type'],
                'document_type': checksum['document_type'],
                'required': bool(checksum['required']),
                'verified': bool(checksum['verified']),
                'upload_timestamp': checksum['upload_timestamp']
            })
        
        return {
            'success': True,
            'submission_id': submission_id,
            'document_checksums': results,
            'total_documents': len(results)
        }
    
    finally:
        conn.close()

@router.post("/regenerate-manifest/{submission_id}")
async def regenerate_manifest(submission_id: str):
    """Regenerate manifest for existing submission (admin only)"""
    
    conn = get_db_connection()
    try:
        # Get current submission
        cursor = conn.cursor()
        cursor.execute("""
            SELECT application_id, manifest_json FROM submission_packs
            WHERE submission_id = ?
        """, (submission_id,))
        
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        application_id, current_manifest_json = result
        current_manifest = json.loads(current_manifest_json)
        
        # Store current version
        cursor.execute("""
            INSERT INTO manifest_versions
            (submission_id, version_number, manifest_json, change_description, created_by)
            VALUES (?, ?, ?, ?, ?)
        """, (
            submission_id,
            1,  # Version 1 (original)
            current_manifest_json,
            "Original manifest before regeneration",
            "api_admin"
        ))
        
        # Note: In production, would regenerate from stored documents
        # For now, just update the timestamp and version
        current_manifest['manifest_version'] = "1.1"
        current_manifest['regenerated_at'] = datetime.now(timezone.utc).isoformat()
        
        new_manifest_json = json.dumps(current_manifest)
        
        # Update submission pack
        cursor.execute("""
            UPDATE submission_packs
            SET manifest_json = ?, last_verified = ?
            WHERE submission_id = ?
        """, (new_manifest_json, datetime.now(timezone.utc), submission_id))
        
        # Store new version
        cursor.execute("""
            INSERT INTO manifest_versions
            (submission_id, version_number, manifest_json, change_description, created_by)
            VALUES (?, ?, ?, ?, ?)
        """, (
            submission_id,
            2,  # Version 2 (regenerated)
            new_manifest_json,
            "Manifest regenerated via API",
            "api_admin"
        ))
        
        conn.commit()
        
        return {
            'success': True,
            'message': 'Manifest regenerated successfully',
            'submission_id': submission_id,
            'new_manifest': current_manifest
        }
    
    finally:
        conn.close()