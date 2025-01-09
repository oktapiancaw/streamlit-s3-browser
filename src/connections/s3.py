import boto3

from loguru import logger

from models.base import S3ConnectionMeta


class S3HttpConnector:
    def __init__(self, meta: S3ConnectionMeta) -> None:
        self._meta: S3ConnectionMeta = meta
        self.client = None
        self.bucket = meta.bucket

    def connect(self, **kwargs):
        try:
            self.client = boto3.client(
                "s3",
                endpoint_url=f"http://{self._meta.host}:{self._meta.port}",
                aws_access_key_id=self._meta.access_key,
                aws_secret_access_key=self._meta.secret_key,
            )
            logger.success("S3HTTP is connected")
        except Exception:
            raise ValueError("Failed to connect to S3HTTP")

    @property
    def s3_meta(self):
        return {
            "endpoint_url": f"http://{self._meta.host}:{self._meta.port}",
            "aws_access_key_id": self._meta.access_key,
            "aws_secret_access_key": self._meta.secret_key,
        }

    def close(self):
        if self.client:
            self.client.close()
        logger.success("S3HTTP is closed")
