import logging

import opendal
from typica import S3ConnectionMeta

from src.configs import CustomLogLevel

LOGGER = logging.getLogger(__name__)


class OpenDALConnector:
    def __init__(self, meta: S3ConnectionMeta) -> None:
        self._meta: S3ConnectionMeta = meta
        self.operator: opendal.AsyncOperator = None
        self.bucket = meta.bucket

    def connect(self):
        """
        Initializes the OpenDAL AsyncOperator.
        OpenDAL doesn't 'handshake' on init, it validates on the first call.
        """
        try:
            self.operator = opendal.AsyncOperator(
                "s3",
                endpoint=self._meta.endpoint,
                access_key_id=self._meta.access_key,
                secret_access_key=self._meta.secret_key,
                bucket=self._meta.bucket,
                region="us-east-1",
                enable_virtual_host_style="false",
            )
            LOGGER.log(CustomLogLevel.CONNECTION, "OpenDAL S3 Connector initialized")
        except Exception as e:
            LOGGER.error(f"Failed to initialize OpenDAL: {e}")
            raise ValueError("Failed to connect to S3 via OpenDAL")

    @property
    def s3_meta(self):
        return {
            "endpoint": self._meta.endpoint,
            "bucket": self._meta.bucket,
            "access_key_id": self._meta.access_key,
        }

    async def list_dir_contents(self, path: str = "", recursive: bool = False):
        path = path if path.endswith("/") else path + "/"
        lister = await self.operator.list(path, recursive=recursive)
        file_result = []
        dir_result = []
        async for entry in lister:
            meta = entry.metadata
            if meta.mode.is_file():
                file_result.append(
                    {
                        "FullPath": f"{self._meta.endpoint}/{self._meta.bucket}/{entry.path}",
                        "Key": entry.path,
                        "Size": meta.content_length,
                        "SizeInKB": str(round(meta.content_length / 1024, 2)) + "KB",
                        "LastModified": meta.last_modified.strftime(
                            "%A, %d %B %Y %H:%M"
                        )
                        if meta.last_modified
                        else None,
                        "ContentType": meta.content_type,
                    }
                )
            else:
                dir_result.append(
                    {
                        "Name": entry.path.replace(path, ""),
                        "Key": entry.path,
                        "Size": meta.content_length,
                        "LastModified": meta.last_modified,
                    }
                )

        return file_result, dir_result

    async def read_file(self, path: str) -> bytes:
        """
        Reads file content as bytes.
        """
        return await self.operator.read(path)

    def close(self):
        """
        OpenDAL handles its own resource cleanup,
        but we can nullify the operator to be safe.
        """
        self.operator = None
        LOGGER.log(CustomLogLevel.CONNECTION, "OpenDAL S3 Connector session cleared")
