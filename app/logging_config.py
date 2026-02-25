import logging
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s %(levelname)-8s %(name)s %(message)s",
        },
    },
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "ai_trade": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["default"],
        "level": "WARNING",
    },
}

def setup_logging() -> None:
    logging.config.dictConfig(LOGGING_CONFIG)

logger = logging.getLogger("ai_trade")
