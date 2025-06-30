import os
from pathlib import Path
import logging
import logging.config

from celery.signals import after_setup_logger, after_setup_task_logger

# We only want Celery’s dictConfig when this code is running in a Celery worker.
# Use an environment variable (set in your Celery Docker container) to signal that.
RUN_CELERY_LOGGING = os.getenv("RUNNING_AS_CELERY", "false").lower() == "true"

SERVICE_NAME = os.getenv("SERVICE_NAME", "tasks_server")

@after_setup_logger.connect
# @after_setup_task_logger.connect
def _configure_logging(logger: logging.Logger, *args, **kwargs) -> None:
    if RUN_CELERY_LOGGING:
        LOG_LEVEL    = os.getenv("LOG_LEVEL", "INFO").upper()
        LOGFILE_NAME = os.getenv("LOGFILE_NAME", "combined_server.log")
        # Inside the container, as /data/logs
        log_folder = Path("/data/logs")
        if not log_folder.exists():
            log_folder.mkdir(parents=True, exist_ok=True)
        LOGFILE_PATH = log_folder.joinpath(LOGFILE_NAME)

        logging.config.dictConfig({
            "version": 1,
            "disable_existing_loggers": False,

            # We define a formatter exactly like FastAPI’s, so everything looks uniform.
            "formatters": {
                "default": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },

            # Only configure handlers that affect "celery" and its children. We do NOT reconfigure the root logger here.
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "level": LOG_LEVEL,
                },
                "file": {
                    "class": "logging.FileHandler",
                    "formatter": "default",
                    "level": LOG_LEVEL,
                    "filename": LOGFILE_PATH,
                    "mode": "a",
                },
            },

            "loggers": {
                # Celery’s own logger hierarchy:
                "celery": {
                    "handlers": ["console", "file"],
                    "level": LOG_LEVEL,
                    "propagate": False,
                },
                # Include this if you want task‐trace logs too:
                "celery.app.trace": {
                    "handlers": ["console", "file"],
                    "level": LOG_LEVEL,
                    "propagate": False,
                },
                
                # Quiet down MODULES to INFO (or WARNING) instead of DEBUG
                "celery.bootsteps": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
                
                "celery.worker.consumer": {
                    "handlers": ["console", "file"],
                    "level": "WARNING",
                    "propagate": False,
                },
                "celery.concurrency": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
                
                "mmpycorex.launcher": {
                    "handlers": ["console", "file"],
                    "level": "WARNING",
                    "propagate": False,
                },
            }
            # NOTE: we do NOT touch "root" here, so FastAPI’s root config remains intact.
        })

        # Optional: a quick sanity‐check message
        _celery_logger = logging.getLogger(f"{SERVICE_NAME}.logging")
        _celery_logger.info(
            "Celery logging configured (console + %s) at level %s",
            LOGFILE_PATH, LOG_LEVEL)

# Provide a wrapper to fetch a named logger under our “tasks_server” umbrella.
def get_logger(name: str = None) -> logging.Logger:
    """
    Returns a logger whose name is prefixed by 'tasks_server' (or whatever SERVICE_NAME).
    If name=None, returns the 'tasks_server' logger itself.
    """
    base = SERVICE_NAME
    return logging.getLogger(f"{base}.{name}") if name else logging.getLogger(base)
