"""Application logging configuration and utilities."""

import logging
import sys
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configures structured logging for the application."""
    log_format = "%(asctime)s - [%(levelname)s] - [%(name)s] - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Silence verbose 3rd party logs if not in DEBUG
    if not settings.DEBUG:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logger = logging.getLogger("eve_healthcare")
    logger.info("Logging configured with level: %s", settings.LOG_LEVEL.upper())
    return logger


logger = setup_logging()
