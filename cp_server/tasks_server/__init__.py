import os
import logging
import logging.config

# We only want Celery’s dictConfig when this code is running in a Celery worker.
# Use an environment variable (set in your Celery Docker container) to signal that.
RUN_CELERY_LOGGING = os.getenv("RUNNING_AS_CELERY", "false").lower() == "true"

# Always read (and default) the SERVICE_NAME from the environment.
# In the Celery container yit will do: SERVICE_NAME=celery-default
# In the FastAPI container, SERVICE_NAME will be "fastapi" (or whatever is set).
SERVICE_NAME = os.getenv("SERVICE_NAME", "tasks_server")

if RUN_CELERY_LOGGING:
    LOG_LEVEL    = os.getenv("LOG_LEVEL", "INFO").upper()
    LOGFILE_NAME = os.getenv("LOGFILE_NAME", "combined_server.log")
    # /logs is mounted from host's ./logs
    LOGFILE_PATH = os.path.join("/logs", LOGFILE_NAME)

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,

        # We define a formatter exactly like FastAPI’s, so everything looks uniform.
        "formatters": {
            "default": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
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
        }
        # NOTE: we do NOT touch "root" here, so FastAPI’s root config remains intact.
    })

    # Optional: a quick sanity‐check message
    _celery_logger = logging.getLogger("celery.logging")
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
