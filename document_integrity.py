#!/usr/bin/env python3
"""
Document bundling and integrity services for submission packs
"""

import os
import json
import hashlib
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

class DocumentBundleService:
    @staticmethod
    def calculate_sha256(file_path: str) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes"""
        return os.path.getsize(file_path)
    
    @staticmethod
    def generate_manifest(files: List[Dict[str, Any]], pack_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate manifest.json with file integrity data"""
        manifest = {
            "submission_pack": {
                "id": pack_metadata.get("pack_id"),
                "title": pack_metadata.get("title"),
                "project_name": pack_metadata.get("project_name"),
                "created_at": datetime.now().isoformat(),
                "created_by": pack_metadata.get("created_by"),
                "version": "1.0"
            },
            "integrity": {
                "total_files": len(files),
                "total_size_bytes": sum(f["size_bytes"] for f in files),
                "manifest_version": "2.1.0",
                "hash_algorithm": "SHA256"
            },
            "files": files,
            "metadata": {
                "model_version": pack_metadata.get("model_version", "domus-docs-v2.1.0"),
                "data_freshness": pack_metadata.get("data_freshness", {}),
                "generation_timestamp": datetime.now().isoformat(),
                "platform": "Domus Planning Intelligence"
            },
            "authority_context": pack_metadata.get("authority_context", {}),
            "verification": {
                "checksum_algorithm": "SHA256",
                "manifest_checksum": "",  # Will be calculated after manifest creation
                "verification_instructions": "Verify file integrity by recalculating SHA256 checksums and comparing with manifest values"
            }
        }
        
        return manifest
    
    @staticmethod
    def create_submission_pack(
        files_to_bundle: List[str], 
        output_path: str, 
        pack_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create ZIP submission pack with manifest and integrity checking"""
        try:
            files_info = []
            temp_manifest_path = "/tmp/manifest.json"
            
            # Process each file and collect metadata
            for file_path in files_to_bundle:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"File not found: {file_path}")
                
                file_info = {
                    "filename": os.path.basename(file_path),
                    "path": os.path.basename(file_path),  # Relative path in ZIP
                    "size_bytes": DocumentBundleService.get_file_size(file_path),
                    "sha256": DocumentBundleService.calculate_sha256(file_path),
                    "created_at": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                    "modified_at": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                    "mime_type": DocumentBundleService.get_mime_type(file_path)
                }
                files_info.append(file_info)
            
            # Generate manifest
            manifest = DocumentBundleService.generate_manifest(files_info, pack_metadata)
            
            # Calculate manifest checksum
            manifest_json = json.dumps(manifest, sort_keys=True, indent=2)
            manifest["verification"]["manifest_checksum"] = hashlib.sha256(manifest_json.encode()).hexdigest()
            
            # Write manifest to temp file
            with open(temp_manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            # Create ZIP file
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add manifest first
                zipf.write(temp_manifest_path, "manifest.json")
                
                # Add all other files
                for file_path in files_to_bundle:
                    arcname = os.path.basename(file_path)
                    zipf.write(file_path, arcname)
            
            # Clean up temp manifest
            os.remove(temp_manifest_path)
            
            # Calculate final ZIP checksum
            zip_checksum = DocumentBundleService.calculate_sha256(output_path)
            
            return {
                "success": True,
                "pack_path": output_path,
                "manifest": manifest,
                "zip_checksum": zip_checksum,
                "total_files": len(files_to_bundle) + 1,  # +1 for manifest
                "total_size": os.path.getsize(output_path)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def get_mime_type(file_path: str) -> str:
        """Get MIME type based on file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.txt': 'text/plain',
            '.csv': 'text/csv',
            '.xml': 'application/xml',
            '.json': 'application/json'
        }
        return mime_types.get(ext, 'application/octet-stream')

class IntegrityVerificationService:
    @staticmethod
    def verify_submission_pack(zip_path: str) -> Dict[str, Any]:
        """Verify integrity of a submission pack"""
        try:
            verification_results = {
                "pack_valid": True,
                "manifest_valid": True,
                "files_verified": 0,
                "files_failed": 0,
                "errors": [],
                "manifest": None,
                "file_results": []
            }
            
            # Extract and verify ZIP
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                # Check if manifest exists
                if 'manifest.json' not in zipf.namelist():
                    verification_results["pack_valid"] = False
                    verification_results["errors"].append("manifest.json not found in submission pack")
                    return verification_results
                
                # Read manifest
                with zipf.open('manifest.json') as manifest_file:
                    manifest = json.load(manifest_file)
                    verification_results["manifest"] = manifest
                
                # Verify each file listed in manifest
                for file_info in manifest.get("files", []):
                    filename = file_info["filename"]
                    expected_sha256 = file_info["sha256"]
                    expected_size = file_info["size_bytes"]
                    
                    if filename not in zipf.namelist():
                        verification_results["files_failed"] += 1
                        verification_results["file_results"].append({
                            "filename": filename,
                            "status": "missing",
                            "error": "File not found in ZIP"
                        })
                        continue
                    
                    # Extract file to temporary location for verification
                    with zipf.open(filename) as file_data:
                        content = file_data.read()
                        
                        # Verify size
                        actual_size = len(content)
                        if actual_size != expected_size:
                            verification_results["files_failed"] += 1
                            verification_results["file_results"].append({
                                "filename": filename,
                                "status": "size_mismatch",
                                "expected_size": expected_size,
                                "actual_size": actual_size
                            })
                            continue
                        
                        # Verify SHA256
                        actual_sha256 = hashlib.sha256(content).hexdigest()
                        if actual_sha256 != expected_sha256:
                            verification_results["files_failed"] += 1
                            verification_results["file_results"].append({
                                "filename": filename,
                                "status": "checksum_mismatch",
                                "expected_sha256": expected_sha256,
                                "actual_sha256": actual_sha256
                            })
                            continue
                        
                        # File verified successfully
                        verification_results["files_verified"] += 1
                        verification_results["file_results"].append({
                            "filename": filename,
                            "status": "verified",
                            "sha256": actual_sha256,
                            "size_bytes": actual_size
                        })
            
            # Set overall validity
            verification_results["pack_valid"] = verification_results["files_failed"] == 0
            
            return verification_results
            
        except Exception as e:
            return {
                "pack_valid": False,
                "manifest_valid": False,
                "files_verified": 0,
                "files_failed": 0,
                "errors": [f"Verification failed: {str(e)}"],
                "manifest": None,
                "file_results": []
            }