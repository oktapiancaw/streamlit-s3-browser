import re

from typica import HostMeta, Optional, Field, model_validator


class S3ConnectionMeta(HostMeta):
    endpoint_uri: Optional[str] = Field(default=None)
    access_key: str
    secret_key: str
    bucket: str

    @model_validator(mode="after")
    def extract_uri(self):
        if self.endpoint_uri:
            uri = re.sub(r"\w+:(//|/)", "", self.endpoint_uri)
            metadata, _ = (
                re.split(r"\/\?|\/", uri) if re.search(r"\/\?|\/", uri) else [uri, None]
            )
            if "@" in metadata:
                self.username, self.password, self.host, self.port = re.split(
                    r"\@|\:", metadata
                )
            else:
                self.host, self.port = re.split(r"\:", metadata)
            self.port = int(self.port)
        return self
