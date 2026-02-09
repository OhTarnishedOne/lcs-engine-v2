import logging
import sys

from ..settings import get_settings

settings = get_settings()


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("lcs_engine")
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, settings.log_level.upper()))

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


logger = setup_logging()
