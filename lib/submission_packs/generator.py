"""
Submission Pack Generator
Generates secure document submission packs with manifest.json and SHA256 checksums
"""

import hashlib
import json
import os
import zipfile
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile
import logging

# Try to import boto3, fall back to mock for testing
try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    from .mock_s3 import mock_boto3_client as boto3_client, MockClientError as ClientError
    BOTO3_AVAILABLE = False
    print("⚠️ boto3 not available, using mock S3 for testing")

logger = logging.getLogger(__name__)

@dataclass
class DocumentChecksum:
    """Individual document checksum information"""
    filename: str
    original_name: str
    file_size: int
    sha256_hash: str
    mime_type: str
    upload_timestamp: str
    document_type: str  # planning_drawings, design_statement, heritage_statement, etc.
    required: bool
    verified: bool = False

@dataclass
class SubmissionManifest:
    """Complete submission pack manifest"""
    submission_id: str
    application_reference: str
    lpa_code: str
    applicant_name: str
    property_address: str
    application_type: str
    submission_timestamp: str
    documents: List[DocumentChecksum]
    total_documents: int
    total_size_bytes: int
    manifest_version: str = "1.0"
    integrity_verified: bool = False
    
class SubmissionPackGenerator:
    """Generates secure submission packs with manifest and checksums"""
    
    def __init__(self, s3_bucket: str = "domus-submission-packs"):
        self.s3_bucket = s3_bucket
        
        # Initialize S3 client (real or mock)
        if BOTO3_AVAILABLE:
            self.s3_client = boto3.client('s3')
        else:
            self.s3_client = boto3_client('s3')
        
        # Required document types for different application types
        self.required_documents = {
            "householder": [
                "application_form",
                "location_plan", 
                "site_plan",
                "existing_drawings",
                "proposed_drawings"
            ],
            "full_planning": [
                "application_form",
                "location_plan",
                "site_plan", 
                "existing_drawings",
                "proposed_drawings",
                "design_statement",
                "planning_statement"
            ],
            "listed_building": [
                "application_form",
                "location_plan",
                "site_plan",
                "existing_drawings", 
                "proposed_drawings",
                "heritage_statement",
                "design_statement"
            ]
        }
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def detect_mime_type(self, file_path: str) -> str:
        """Detect MIME type based on file extension"""
        extension = Path(file_path).suffix.lower()
        
        mime_types = {
            '.pdf': 'application/pdf',
            '.dwg': 'application/acad',
            '.dxf': 'application/dxf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        
        return mime_types.get(extension, 'application/octet-stream')
    
    def categorize_document(self, filename: str) -> str:
        """Categorize document based on filename patterns"""
        filename_lower = filename.lower()
        
        # Pattern matching for document types
        if any(term in filename_lower for term in ['location', 'site_location']):
            return 'location_plan'
        elif any(term in filename_lower for term in ['site_plan', 'site plan']):
            return 'site_plan'
        elif any(term in filename_lower for term in ['existing', 'current']):
            return 'existing_drawings'
        elif any(term in filename_lower for term in ['proposed', 'new']):
            return 'proposed_drawings'
        elif any(term in filename_lower for term in ['design', 'design_statement']):
            return 'design_statement'
        elif any(term in filename_lower for term in ['planning', 'planning_statement']):
            return 'planning_statement'
        elif any(term in filename_lower for term in ['heritage', 'heritage_statement']):
            return 'heritage_statement'
        elif any(term in filename_lower for term in ['application', 'form']):
            return 'application_form'
        else:
            return 'supporting_document'
    
    def validate_document_requirements(self, documents: List[DocumentChecksum], 
                                     application_type: str) -> Tuple[bool, List[str]]:
        """Validate that all required documents are present"""
        required_docs = self.required_documents.get(application_type, [])
        provided_types = {doc.document_type for doc in documents}
        
        missing_docs = [doc_type for doc_type in required_docs 
                       if doc_type not in provided_types]
        
        is_valid = len(missing_docs) == 0
        return is_valid, missing_docs
    
    def create_document_checksum(self, file_path: str, original_name: str, 
                               document_type: str, required: bool = False) -> DocumentChecksum:
        """Create checksum record for a single document"""
        file_stats = os.stat(file_path)
        
        return DocumentChecksum(
            filename=Path(file_path).name,
            original_name=original_name,
            file_size=file_stats.st_size,
            sha256_hash=self.calculate_file_hash(file_path),
            mime_type=self.detect_mime_type(file_path),
            upload_timestamp=datetime.now(timezone.utc).isoformat(),
            document_type=document_type,
            required=required
        )
    
    def generate_submission_pack(self, 
                               submission_id: str,
                               application_reference: str,
                               lpa_code: str,
                               applicant_name: str,
                               property_address: str,
                               application_type: str,
                               document_paths: List[Tuple[str, str]]) -> SubmissionManifest:
        """
        Generate complete submission pack with manifest
        
        Args:
            document_paths: List of (file_path, original_name) tuples
        """
        
        documents = []
        total_size = 0
        required_docs = self.required_documents.get(application_type, [])
        
        # Process each document
        for file_path, original_name in document_paths:
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                continue
                
            # Categorize and create checksum
            doc_type = self.categorize_document(original_name)
            is_required = doc_type in required_docs
            
            doc_checksum = self.create_document_checksum(
                file_path, original_name, doc_type, is_required
            )
            
            documents.append(doc_checksum)
            total_size += doc_checksum.file_size
        
        # Create manifest
        manifest = SubmissionManifest(
            submission_id=submission_id,
            application_reference=application_reference,
            lpa_code=lpa_code,
            applicant_name=applicant_name,
            property_address=property_address,
            application_type=application_type,
            submission_timestamp=datetime.now(timezone.utc).isoformat(),
            documents=documents,
            total_documents=len(documents),
            total_size_bytes=total_size
        )
        
        # Validate requirements
        is_valid, missing_docs = self.validate_document_requirements(documents, application_type)
        manifest.integrity_verified = is_valid
        
        if not is_valid:
            logger.warning(f"Missing required documents for {application_type}: {missing_docs}")
        
        return manifest
    
    def create_submission_zip(self, manifest: SubmissionManifest, 
                            document_paths: List[Tuple[str, str]],
                            output_dir: str = None) -> str:
        """Create ZIP file with documents and manifest"""
        
        if output_dir is None:
            output_dir = tempfile.gettempdir()
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        zip_filename = f"submission_{manifest.submission_id}_{manifest.application_reference.replace('/', '_')}.zip"
        zip_path = os.path.join(output_dir, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add manifest.json
            manifest_json = json.dumps(asdict(manifest), indent=2, ensure_ascii=False)
            zipf.writestr('manifest.json', manifest_json)
            
            # Add all documents
            for file_path, original_name in document_paths:
                if os.path.exists(file_path):
                    # Use original filename in ZIP
                    zipf.write(file_path, original_name)
        
        logger.info(f"Created submission ZIP: {zip_path}")
        return zip_path
    
    def upload_to_s3(self, zip_path: str, manifest: SubmissionManifest) -> str:
        """Upload submission pack to S3"""
        
        # S3 key structure: lpa_code/year/month/submission_id/
        timestamp = datetime.fromisoformat(manifest.submission_timestamp.replace('Z', '+00:00'))
        s3_key = f"{manifest.lpa_code}/{timestamp.year}/{timestamp.month:02d}/{manifest.submission_id}/{Path(zip_path).name}"
        
        try:
            # Upload ZIP file
            self.s3_client.upload_file(
                zip_path, 
                self.s3_bucket, 
                s3_key,
                ExtraArgs={
                    'Metadata': {
                        'submission-id': manifest.submission_id,
                        'application-reference': manifest.application_reference,
                        'lpa-code': manifest.lpa_code,
                        'application-type': manifest.application_type,
                        'document-count': str(manifest.total_documents),
                        'total-size': str(manifest.total_size_bytes),
                        'integrity-verified': str(manifest.integrity_verified)
                    },
                    'ServerSideEncryption': 'AES256'
                }
            )
            
            # Also upload manifest separately for quick access
            manifest_key = s3_key.replace('.zip', '_manifest.json')
            manifest_json = json.dumps(asdict(manifest), indent=2, ensure_ascii=False)
            
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=manifest_key,
                Body=manifest_json,
                ContentType='application/json',
                ServerSideEncryption='AES256'
            )
            
            s3_url = f"s3://{self.s3_bucket}/{s3_key}"
            logger.info(f"Uploaded submission pack to S3: {s3_url}")
            return s3_url
            
        except ClientError as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise
    
    def verify_submission_integrity(self, zip_path: str) -> Tuple[bool, List[str]]:
        """Verify integrity of submission pack by checking all hashes"""
        
        errors = []
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                # Read manifest
                manifest_data = zipf.read('manifest.json')
                manifest_dict = json.loads(manifest_data)
                manifest = SubmissionManifest(**manifest_dict)
                
                # Verify each document hash
                for doc in manifest.documents:
                    try:
                        # Extract file to temp location
                        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                            temp_file.write(zipf.read(doc.original_name))
                            temp_path = temp_file.name
                        
                        # Calculate hash
                        actual_hash = self.calculate_file_hash(temp_path)
                        
                        if actual_hash != doc.sha256_hash:
                            errors.append(f"Hash mismatch for {doc.original_name}: expected {doc.sha256_hash}, got {actual_hash}")
                        
                        # Clean up temp file
                        os.unlink(temp_path)
                        
                    except KeyError:
                        errors.append(f"Missing file in ZIP: {doc.original_name}")
                    except Exception as e:
                        errors.append(f"Error verifying {doc.original_name}: {str(e)}")
        
        except Exception as e:
            errors.append(f"Failed to read ZIP file: {str(e)}")
        
        is_valid = len(errors) == 0
        return is_valid, errors

class SubmissionPackManager:
    """Manages submission pack lifecycle and verification"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.generator = SubmissionPackGenerator()
    
    def create_submission_pack(self, application_id: str, document_files: List[Dict]) -> Dict:
        """Create submission pack for an application"""
        
        # Get application details from database
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT application_reference, lpa_code, applicant_name, 
                   property_address, application_type
            FROM applications 
            WHERE id = ?
        """, (application_id,))
        
        app_data = cursor.fetchone()
        if not app_data:
            raise ValueError(f"Application {application_id} not found")
        
        app_ref, lpa_code, applicant_name, property_address, app_type = app_data
        
        # Prepare document paths
        document_paths = []
        for doc_file in document_files:
            file_path = doc_file.get('file_path')
            original_name = doc_file.get('original_name')
            if file_path and original_name:
                document_paths.append((file_path, original_name))
        
        # Generate submission ID
        submission_id = f"SUB_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{application_id}"
        
        # Generate manifest
        manifest = self.generator.generate_submission_pack(
            submission_id=submission_id,
            application_reference=app_ref,
            lpa_code=lpa_code,
            applicant_name=applicant_name,
            property_address=property_address,
            application_type=app_type,
            document_paths=document_paths
        )
        
        # Create ZIP file
        zip_path = self.generator.create_submission_zip(manifest, document_paths)
        
        # Upload to S3
        s3_url = self.generator.upload_to_s3(zip_path, manifest)
        
        # Store submission record in database
        cursor.execute("""
            INSERT INTO submission_packs 
            (submission_id, application_id, application_reference, 
             s3_url, manifest_json, total_documents, total_size_bytes,
             integrity_verified, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            submission_id, application_id, app_ref,
            s3_url, json.dumps(asdict(manifest)),
            manifest.total_documents, manifest.total_size_bytes,
            manifest.integrity_verified, datetime.now(timezone.utc)
        ))
        
        self.db.commit()
        
        # Clean up local ZIP file
        os.unlink(zip_path)
        
        return {
            'submission_id': submission_id,
            'manifest': manifest,
            's3_url': s3_url,
            'integrity_verified': manifest.integrity_verified,
            'total_documents': manifest.total_documents,
            'total_size_mb': round(manifest.total_size_bytes / (1024 * 1024), 2)
        }
    
    def verify_submission_pack(self, submission_id: str) -> Dict:
        """Download and verify submission pack integrity"""
        
        # Get submission details
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT s3_url, manifest_json 
            FROM submission_packs 
            WHERE submission_id = ?
        """, (submission_id,))
        
        result = cursor.fetchone()
        if not result:
            raise ValueError(f"Submission {submission_id} not found")
        
        s3_url, manifest_json = result
        
        # Download from S3 to temp file
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Extract S3 key from URL
            s3_key = s3_url.replace(f"s3://{self.generator.s3_bucket}/", "")
            
            # Download file
            self.generator.s3_client.download_file(
                self.generator.s3_bucket, 
                s3_key, 
                temp_path
            )
            
            # Verify integrity
            is_valid, errors = self.generator.verify_submission_integrity(temp_path)
            
            # Update verification status
            cursor.execute("""
                UPDATE submission_packs 
                SET integrity_verified = ?, verification_errors = ?, 
                    last_verified = ?
                WHERE submission_id = ?
            """, (is_valid, json.dumps(errors), datetime.now(timezone.utc), submission_id))
            
            self.db.commit()
            
            return {
                'submission_id': submission_id,
                'integrity_verified': is_valid,
                'errors': errors,
                'verification_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)