from pathlib import Path
import os
import logging
import logging.config

# Read level and filename from environment (populated via your docker-compose/.env)
LOG_LEVEL     = os.getenv("LOG_LEVEL", "INFO").upper()
LOGFILE_NAME  = os.getenv("LOGFILE_NAME", "combined_server.log")
SERVICE_NAME  = os.getenv("SERVICE_NAME", "fastapi_app")

# Inside the container, as /data/logs
log_folder = Path("/data/logs")
if not log_folder.exists():
    log_folder.mkdir(parents=True, exist_ok=True)
LOGFILE_PATH  = log_folder.joinpath(LOGFILE_NAME)

# 1) Build a dictConfig that attaches both console and file handlers
logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        # → send everything to stdout/stderr so Docker captures it
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": LOG_LEVEL,
        },
        # → also append to /logs/<combined_server.log> inside container (→ host’s ./logs/)
        "file": {
            "class": "logging.FileHandler",
            "formatter": "default",
            "level": LOG_LEVEL,
            "filename": LOGFILE_PATH,
            "mode": "a",
        },
    },
    # 2) Apply to the root logger
    "root": {
        "handlers": ["console", "file"],
        "level": LOG_LEVEL,
    },
})

def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger with the name of the service with/without a specific name.
    If `name` is provided, it will be prefixed with the service name.
    If `name` is None, it returns the root logger for the service.
    This logger will log to both stdout and a file at /logs/<combined_server.log>.
    The log file is stored in the HOST_LOG_FOLDER, which should be mounted as a volume
    in the Docker container.
    The log file will be created if it does not exist, and it will append to the file
    if it does.
    The log format is set to include the timestamp, log level, logger name, and message.
    The date format is set to "YYYY-MM-DD HH:MM:SS".
    
    :param name: Optional name for the logger. If provided, it will be prefixed with the service name.
    
    :return: A configured logger instance.
    """
    base = SERVICE_NAME
    return logging.getLogger(f"{base}.{name}") if name else logging.getLogger(base)

# At this point, any logger.getLogger(...) under fastapi_app (or even outside it) 
# inherits these two handlers. If you want a quick confirmation, you can log:
logger = get_logger('logger')
logger.info("FastAPI package logging set up (console ↔ %s)", LOGFILE_PATH)
