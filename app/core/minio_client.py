from contextlib import asynccontextmanager

import aioboto3

from app.core.config import Settings

settings = Settings()


class S3Service:
    def __init__(self):
        self.session = aioboto3.Session(
            aws_access_key_id=settings.S3_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET,
        )
        self.bucket_name = settings.S3_BUCKET_NAME
        self.endpoint_url = settings.S3_ENDPOINT_URL

    @asynccontextmanager
    async def get_client(self):
        async with self.session.client("s3", endpoint_url=self.endpoint_url) as client:
            yield client

    async def upload_file(self, file_bytes: bytes, object_name: str) -> str:
        async with self.get_client() as client:
            await client.put_object(
                Bucket=self.bucket_name, Key=object_name, Body=file_bytes
            )
        return object_name

    async def get_file_url(self, object_name: str) -> str:
        async with self.get_client() as client:
            url = await client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_name},
                ExpiresIn=3600,
            )
        return url


s3_service = S3Service()


def get_s3_service() -> S3Service:
    return s3_service
