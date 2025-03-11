from .env import ApplicationConfig, ProjectConfig
from loguru import logger as LOGGER

config = ApplicationConfig()
poetry_config = ProjectConfig()
