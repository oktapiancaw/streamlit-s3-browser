import re

from typica import EndpointMeta, Optional, Field, model_validator


class S3ConnectionMeta(EndpointMeta):
    endpoint_url: Optional[str] = Field(default=None)
    access_key: str
    secret_key: str
    bucket: str

    @model_validator(mode="after")
    def extract_uri(self):
        if self.endpoint_url:
            uri = re.sub(r"\w+:(//|/)", "", self.endpoint_url)
            metadata, _ = (
                re.split(r"\/\?|\/", uri) if re.search(r"\/\?|\/", uri) else [uri, None]
            )
            if "@" in metadata:
                self.username, self.password, self.host, self.port = re.split(
                    r"\@|\:", metadata
                )
            else:
                self.host, self.port = re.split(r"\:", metadata)
            if self.port:
                self.port = int(self.port)
        return self
