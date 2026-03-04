from typing import Optional

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
)


class ApplicationConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    CONNECT_DE_STORAGE: Optional[bool] = False
    CONNECT_DE_URL: Optional[str] = None
    CONNECT_DE_DATABASE: Optional[str] = None
    CONNECT_DE_COLLECTION: Optional[str] = None


class ProjectConfig(BaseSettings):
    name: str
    version: str = "0.1.0"
    description: str = ""
    authors: list[dict] = []

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (PyprojectTomlConfigSettingsSource(settings_cls),)

    model_config = SettingsConfigDict(
        pyproject_toml_table_header=("project",), extra="ignore"
    )

    @property
    def title(self) -> str:
        return self.name.replace("-", " ").title()
