"""
Database migration for Submission Packs system
Creates tables for document manifests, checksums, and verification tracking
"""

import sqlite3
from datetime import datetime, timezone

def migrate_submission_packs():
    """Create submission packs database schema"""
    
    conn = sqlite3.connect('dev.db')
    cursor = conn.cursor()
    
    # Submission packs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submission_packs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id TEXT UNIQUE NOT NULL,
            application_id TEXT NOT NULL,
            application_reference TEXT NOT NULL,
            s3_url TEXT NOT NULL,
            manifest_json TEXT NOT NULL,
            total_documents INTEGER NOT NULL,
            total_size_bytes INTEGER NOT NULL,
            integrity_verified BOOLEAN DEFAULT FALSE,
            verification_errors TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_verified TIMESTAMP
        )
    """)
    
    # Create indexes separately
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_submission_id ON submission_packs (submission_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_application_ref ON submission_packs (application_reference)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON submission_packs (created_at)")
    
    # Document checksums table (detailed tracking)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_checksums (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            sha256_hash TEXT NOT NULL,
            mime_type TEXT NOT NULL,
            document_type TEXT NOT NULL,
            required BOOLEAN DEFAULT FALSE,
            verified BOOLEAN DEFAULT FALSE,
            upload_timestamp TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (submission_id) REFERENCES submission_packs (submission_id)
        )
    """)
    
    # Create indexes separately
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_submission_checksums ON document_checksums (submission_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_hash ON document_checksums (sha256_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_type ON document_checksums (document_type)")
    
    # Authority verification logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS authority_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id TEXT NOT NULL,
            lpa_code TEXT NOT NULL,
            verified_by TEXT NOT NULL,
            verification_status TEXT NOT NULL, -- verified, failed, pending
            verification_notes TEXT,
            verification_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (submission_id) REFERENCES submission_packs (submission_id)
        )
    """)
    
    # Create indexes separately
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_authority_verifications ON authority_verifications (submission_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lpa_verifications ON authority_verifications (lpa_code)")
    
    # Document download logs (audit trail)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id TEXT NOT NULL,
            downloaded_by TEXT NOT NULL,
            download_type TEXT NOT NULL, -- full_pack, manifest_only, individual_document
            document_filename TEXT,
            download_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            
            FOREIGN KEY (submission_id) REFERENCES submission_packs (submission_id)
        )
    """)
    
    # Create indexes separately
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_download_logs ON document_downloads (submission_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_download_timestamp ON document_downloads (download_timestamp)")
    
    # Manifest versions (track manifest changes)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS manifest_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id TEXT NOT NULL,
            version_number INTEGER NOT NULL,
            manifest_json TEXT NOT NULL,
            change_description TEXT,
            created_by TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (submission_id) REFERENCES submission_packs (submission_id),
            UNIQUE (submission_id, version_number)
        )
    """)
    
    # Create indexes separately
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_manifest_versions ON manifest_versions (submission_id)")
    
    # S3 upload logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS s3_upload_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id TEXT NOT NULL,
            s3_bucket TEXT NOT NULL,
            s3_key TEXT NOT NULL,
            upload_status TEXT NOT NULL, -- success, failed, in_progress
            file_size_bytes INTEGER,
            upload_duration_seconds REAL,
            error_message TEXT,
            upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (submission_id) REFERENCES submission_packs (submission_id)
        )
    """)
    
    # Create indexes separately
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_s3_uploads ON s3_upload_logs (submission_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_s3_status ON s3_upload_logs (upload_status)")
    
    print("✅ Created submission_packs table")
    print("✅ Created document_checksums table")
    print("✅ Created authority_verifications table") 
    print("✅ Created document_downloads table")
    print("✅ Created manifest_versions table")
    print("✅ Created s3_upload_logs table")
    
    # Insert sample data for testing
    sample_manifest = {
        "submission_id": "SUB_20241004_120000_APP001",
        "application_reference": "E06000001/24/00123/HSE",
        "lpa_code": "E06000001",
        "applicant_name": "John Smith",
        "property_address": "123 High Street, Brighton, BN1 1AA",
        "application_type": "householder",
        "submission_timestamp": datetime.now(timezone.utc).isoformat(),
        "documents": [
            {
                "filename": "location_plan.pdf",
                "original_name": "location_plan.pdf",
                "file_size": 1024000,
                "sha256_hash": "a1b2c3d4e5f6789012345678901234567890abcdef123456789012345678901234",
                "mime_type": "application/pdf",
                "upload_timestamp": datetime.now(timezone.utc).isoformat(),
                "document_type": "location_plan",
                "required": True,
                "verified": False
            },
            {
                "filename": "proposed_drawings.pdf", 
                "original_name": "proposed_drawings.pdf",
                "file_size": 2048000,
                "sha256_hash": "b2c3d4e5f6789012345678901234567890abcdef123456789012345678901234a",
                "mime_type": "application/pdf",
                "upload_timestamp": datetime.now(timezone.utc).isoformat(),
                "document_type": "proposed_drawings",
                "required": True,
                "verified": False
            }
        ],
        "total_documents": 2,
        "total_size_bytes": 3072000,
        "manifest_version": "1.0",
        "integrity_verified": True
    }
    
    import json
    cursor.execute("""
        INSERT OR IGNORE INTO submission_packs 
        (submission_id, application_id, application_reference, s3_url, 
         manifest_json, total_documents, total_size_bytes, integrity_verified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        sample_manifest["submission_id"],
        "APP001",
        sample_manifest["application_reference"],
        f"s3://domus-submission-packs/E06000001/2024/10/{sample_manifest['submission_id']}.zip",
        json.dumps(sample_manifest),
        sample_manifest["total_documents"],
        sample_manifest["total_size_bytes"], 
        sample_manifest["integrity_verified"]
    ))
    
    # Insert document checksums
    for doc in sample_manifest["documents"]:
        cursor.execute("""
            INSERT OR IGNORE INTO document_checksums
            (submission_id, filename, original_name, file_size, sha256_hash,
             mime_type, document_type, required, verified, upload_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sample_manifest["submission_id"],
            doc["filename"],
            doc["original_name"],
            doc["file_size"],
            doc["sha256_hash"],
            doc["mime_type"],
            doc["document_type"],
            doc["required"],
            doc["verified"],
            doc["upload_timestamp"]
        ))
    
    # Insert sample authority verification
    cursor.execute("""
        INSERT OR IGNORE INTO authority_verifications
        (submission_id, lpa_code, verified_by, verification_status, verification_notes)
        VALUES (?, ?, ?, ?, ?)
    """, (
        sample_manifest["submission_id"],
        "E06000001",
        "planning.officer@brighton-hove.gov.uk",
        "verified",
        "All required documents present and checksums verified"
    ))
    
    # Insert sample S3 upload log
    cursor.execute("""
        INSERT OR IGNORE INTO s3_upload_logs
        (submission_id, s3_bucket, s3_key, upload_status, file_size_bytes, upload_duration_seconds)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        sample_manifest["submission_id"],
        "domus-submission-packs",
        f"E06000001/2024/10/{sample_manifest['submission_id']}.zip",
        "success",
        sample_manifest["total_size_bytes"],
        2.5
    ))
    
    conn.commit()
    conn.close()
    
    print("✅ Inserted sample submission pack data")
    print("📦 Sample submission ID: SUB_20241004_120000_APP001")
    print("🏛️ Sample application ref: E06000001/24/00123/HSE")

if __name__ == "__main__":
    migrate_submission_packs()