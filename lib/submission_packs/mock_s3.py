"""
Mock AWS S3 service for testing submission packs without AWS credentials
"""

import os
import json
import tempfile
from typing import Dict, Any

class MockS3Client:
    """Mock S3 client for testing"""
    
    def __init__(self):
        self.uploads = {}
        self.objects = {}
    
    def upload_file(self, local_path: str, bucket: str, key: str, ExtraArgs: Dict = None):
        """Mock S3 upload"""
        if not os.path.exists(local_path):
            raise Exception(f"File not found: {local_path}")
        
        # Store upload metadata
        file_size = os.path.getsize(local_path)
        self.uploads[f"{bucket}/{key}"] = {
            'local_path': local_path,
            'bucket': bucket,
            'key': key,
            'size': file_size,
            'metadata': ExtraArgs.get('Metadata', {}) if ExtraArgs else {}
        }
        
        print(f"✅ Mock S3 upload: {local_path} -> s3://{bucket}/{key} ({file_size} bytes)")
    
    def put_object(self, Bucket: str, Key: str, Body: str, ContentType: str = None, ServerSideEncryption: str = None):
        """Mock S3 put object"""
        self.objects[f"{Bucket}/{Key}"] = {
            'bucket': Bucket,
            'key': Key,
            'body': Body,
            'content_type': ContentType,
            'size': len(Body.encode('utf-8'))
        }
        
        print(f"✅ Mock S3 put object: s3://{Bucket}/{Key} ({len(Body)} characters)")
    
    def download_file(self, bucket: str, key: str, local_path: str):
        """Mock S3 download"""
        upload_key = f"{bucket}/{key}"
        if upload_key in self.uploads:
            # For mock, just copy the original file
            original_path = self.uploads[upload_key]['local_path']
            if os.path.exists(original_path):
                import shutil
                shutil.copy2(original_path, local_path)
                print(f"✅ Mock S3 download: s3://{bucket}/{key} -> {local_path}")
            else:
                raise Exception(f"Original file not found: {original_path}")
        else:
            raise Exception(f"S3 object not found: s3://{bucket}/{key}")

def mock_boto3_client(service_name: str):
    """Mock boto3.client function"""
    if service_name == 's3':
        return MockS3Client()
    else:
        raise Exception(f"Mock client not available for: {service_name}")

# Mock ClientError for testing
class MockClientError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)