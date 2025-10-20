from loguru import logger
import sys
from app.core.config import settings


def configure_logging() -> None:
	logger.remove()
	level = "DEBUG" if settings.env != "prod" else "INFO"
	logger.add(
		sys.stdout,
		level=level,
		format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} | {message}",
	)
