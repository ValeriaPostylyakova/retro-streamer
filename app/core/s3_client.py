from contextlib import asynccontextmanager

import aioboto3
import boto3
from mypy_boto3_s3 import S3Client

from app.core.config import Settings

settings = Settings()


class S3Base:
    def __init__(self):
        self.public_bucket = settings.S3_PUBLIC_BUCKET
        self.private_bucket = settings.S3_PRIVATE_BUCKET
        self.endpoint_url = settings.S3_ENDPOINT_URL

    def _get_bucket_name(self, is_public: bool) -> str:
        return self.public_bucket if is_public else self.private_bucket


class S3AsyncService(S3Base):
    def __init__(self):
        super().__init__()
        self.session = aioboto3.Session(
            aws_access_key_id=settings.S3_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET,
        )

    @asynccontextmanager
    async def get_client(self):
        async with self.session.client("s3", endpoint_url=self.endpoint_url) as client:
            yield client

    async def upload_file(
        self, file_bytes: bytes, object_name: str, is_public: bool = True
    ) -> str:
        bucket = self._get_bucket_name(is_public)
        async with self.get_client() as client:
            await client.put_object(Bucket=bucket, Key=object_name, Body=file_bytes)
        return object_name

    async def get_file_url(self, object_name: str, is_public: bool = True) -> str:
        bucket = self._get_bucket_name(is_public)

        filename = object_name.split("/")[-1]

        async with self.get_client() as client:
            url = await client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": bucket,
                    "Key": object_name,
                    "ResponseContentDisposition": f'attachment; filename="{filename}"',
                },
                ExpiresIn=3600,
            )
        return url


class S3SyncService(S3Base):
    def __init__(self):
        super().__init__()
        self._client: S3Client = boto3.client(
            "s3",
            aws_access_key_id=settings.S3_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET,
            endpoint_url=self.endpoint_url,
        )

    def upload_file_bytes(
        self,
        file_bytes: bytes,
        object_name: str,
        is_public: bool = True,
        content_type: str = "image/gif",
    ) -> None:
        bucket = self._get_bucket_name(is_public)
        self._client.put_object(
            Bucket=bucket,
            Key=object_name,
            Body=file_bytes,
            ContentType=content_type,
        )

    def get_file_url(self, object_name: str, is_public: bool = True) -> str:
        bucket = self._get_bucket_name(is_public)

        filename = object_name.split("/")[-1]

        url = self._client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": bucket,
                "Key": object_name,
                "ResponseContentDisposition": f'attachment; filename="{filename}"',
            },
            ExpiresIn=3600,
        )
        return url


s3_async_client = S3AsyncService()
s3_sync_client = S3SyncService()


def get_s3_async_client() -> S3AsyncService:
    return s3_async_client


def get_s3_sync_client() -> S3SyncService:
    return s3_sync_client
