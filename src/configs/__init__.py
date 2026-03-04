import logging

from typica.utils.log import CustomLogLevel, setup_logger

from .env import ApplicationConfig, ProjectConfig

config = ApplicationConfig()
project_meta = ProjectConfig()


setup_logger(
    **{
        "name": project_meta.name,
        "base_level": CustomLogLevel.DEBUG,
        "console": True,
        "console_level": CustomLogLevel.INFO,
        "log_dir": "./logs",
        "file_handlers_config": [
            {
                "filename": "prod_debug.log",
                "level": CustomLogLevel.DEBUG,
                "max_bytes": 5_000_000,
                "backup_count": 5,
            }
        ],
    }
)

__all__ = [logging, CustomLogLevel, config, ProjectConfig]
