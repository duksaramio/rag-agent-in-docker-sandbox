import boto3
from botocore.client import Config
import logging
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        self.endpoint_url = settings.s3_endpoint_url
        self.bucket_name = settings.s3_bucket_name
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            region_name=settings.s3_region,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"})
        )
        self.ensure_bucket_exists()

    def ensure_bucket_exists(self):
        try:
            buckets = self.s3_client.list_buckets()
            bucket_names = [b["Name"] for b in buckets.get("Buckets", [])]
            if self.bucket_name not in bucket_names:
                logger.info(f"Creating S3 bucket '{self.bucket_name}' in RustFS...")
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"S3 Bucket '{self.bucket_name}' created successfully.")
            else:
                logger.info(f"S3 Bucket '{self.bucket_name}' already exists.")
        except Exception as e:
            logger.error(f"Error ensuring S3 bucket exists on RustFS: {e}")

    def upload_file(self, file_content: bytes, object_name: str, content_type: str = "text/plain") -> str:
        """Upload raw file content to RustFS S3 bucket."""
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=object_name,
            Body=file_content,
            ContentType=content_type
        )
        logger.info(f"Uploaded '{object_name}' to RustFS bucket '{self.bucket_name}'")
        return f"{self.endpoint_url}/{self.bucket_name}/{object_name}"

    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents currently in the gxp-docs bucket."""
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            contents = response.get("Contents", [])
            docs = []
            for item in contents:
                docs.append({
                    "key": item["Key"],
                    "size": item["Size"],
                    "last_modified": item["LastModified"].isoformat()
                })
            return docs
        except Exception as e:
            logger.error(f"Failed to list documents in RustFS bucket: {e}")
            return []

    def get_document_content(self, object_name: str) -> str:
        """Fetch text content of an object from RustFS bucket."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=object_name)
            body = response["Body"].read()
            return body.decode("utf-8", errors="replace")
        except Exception as e:
            logger.error(f"Failed to fetch document '{object_name}' from RustFS: {e}")
            raise e

s3_service = S3Service()
