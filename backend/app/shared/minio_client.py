import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from typing import Optional, List
from ..config import settings


class MinIOClient:

    def __init__(self):
        self.internal_endpoint = settings.MINIO_ENDPOINT
        self.external_endpoint = settings.MINIO_EXTERNAL_ENDPOINT
        self.access_key = settings.MINIO_ACCESS_KEY
        self.secret_key = settings.MINIO_SECRET_KEY
        self.secure = settings.MINIO_SECURE
        self.bucket = settings.MINIO_BUCKET
        self.folder_videos = settings.MINIO_FOLDER_VIDEOS
        self.folder_analytic_videos = settings.MINIO_FOLDER_ANALYTIC_VIDEOS
        self.folder_fragments = settings.MINIO_FOLDER_FRAGMENTS

        self.client = boto3.client(
            's3',
            endpoint_url=f"{'https' if self.secure else 'http'}://{self.internal_endpoint}",
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )

        self.external_client = boto3.client(
            's3',
            endpoint_url=f"{'https' if self.secure else 'http'}://{self.external_endpoint}",
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )

        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        try:
            self.client.head_bucket(Bucket=self.bucket)
            print(f"Bucket '{self.bucket}' already exists")
        except ClientError:
            try:
                self.client.create_bucket(Bucket=self.bucket)
                print(f"Bucket '{self.bucket}' created successfully")
            except Exception as e:
                print(f"Failed to create bucket '{self.bucket}': {e}")

    def _get_full_key(self, object_name: str, folder: str) -> str:
        return f"{folder}/{object_name}"

    def upload_file(
        self,
        file_data: bytes,
        object_name: str,
        folder: str,
        content_type: str = "application/octet-stream"
    ) -> str:
        full_key = self._get_full_key(object_name, folder)

        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=full_key,
                Body=file_data,
                ContentType=content_type
            )
            return full_key
        except Exception as e:
            raise Exception(f"Failed to upload file to MinIO: {e}")

    def download_file(self, object_name: str, folder: str) -> bytes:
        full_key = self._get_full_key(object_name, folder)

        try:
            response = self.client.get_object(Bucket=self.bucket, Key=full_key)
            return response['Body'].read()
        except Exception as e:
            raise Exception(f"Failed to download file from MinIO: {e}")

    def delete_file(self, object_name: str, folder: str) -> bool:
        full_key = self._get_full_key(object_name, folder)

        try:
            self.client.delete_object(Bucket=self.bucket, Key=full_key)
            return True
        except Exception as e:
            print(f"Failed to delete file: {e}")
            return False

    def get_file_url(self, object_name: str, folder: str, expires_in: int = 3600) -> str:
        full_key = self._get_full_key(object_name, folder)

        try:
            url = self.external_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': full_key},
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            raise Exception(f"Failed to generate presigned URL: {e}")

    def get_public_url(self, object_name: str, folder: str) -> str:
        full_key = self._get_full_key(object_name, folder)
        protocol = 'https' if self.secure else 'http'
        return f"{protocol}://{self.external_endpoint}/{self.bucket}/{full_key}"

    def file_exists(self, object_name: str, folder: str) -> bool:
        full_key = self._get_full_key(object_name, folder)

        try:
            self.client.head_object(Bucket=self.bucket, Key=full_key)
            return True
        except ClientError:
            return False

    def list_files(self, folder: str, prefix: str = "") -> List[dict]:
        folder_prefix = f"{folder}/{prefix}" if prefix else f"{folder}/"

        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=folder_prefix
            )
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    file_name = obj['Key'][len(folder_prefix):]
                    if file_name:
                        files.append({
                            'name': file_name,
                            'size': obj['Size'],
                            'last_modified': obj['LastModified']
                        })
            return files
        except Exception as e:
            print(f"Failed to list files: {e}")
            return []


minio_client = MinIOClient()