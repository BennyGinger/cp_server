import os
from pathlib import Path
from logging.config import dictConfig
from celery.signals import after_setup_logger, after_setup_task_logger


# 1) Define a safe default inside your package
_default_logs_dir = Path(__file__).resolve().parent.parent / "logs"

# 2) Try to use the env-var if set
_env_logs = os.getenv("LOG_DIR")
if _env_logs:
    _candidate = Path(_env_logs)
else:
    _candidate = _default_logs_dir

# 3) Ensure we have a writable directory
try:
    _candidate.mkdir(parents=True, exist_ok=True)
    LOGS_DIR = _candidate
except (PermissionError, OSError):
    # fallback to package-local logs
    _default_logs_dir.mkdir(parents=True, exist_ok=True)
    LOGS_DIR = _default_logs_dir

SERVICE_NAME = os.getenv("SERVICE_NAME", "unknown")

LOG_CONFIG = {
    "version": 1,
    "formatters": {
        "default": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
    },
    "handlers": {
        "file": {
            "class":    "logging.FileHandler",
            "formatter":"default",
            "filename": str(LOGS_DIR / f"{SERVICE_NAME}.log"),
            "level":    "DEBUG",
        },
        "stdout": {
            "class":    "logging.StreamHandler",
            "formatter":"default",
            "stream":   "ext://sys.stdout",
            "level":    "DEBUG",
        },
    },
    "root": {
        "handlers": ["file", "stdout"],
        "level":    "DEBUG",
    },
    "loggers": {
            # suppress noisy libraries
            "numba": {"level": "WARNING"},
            "celery": {"level": "WARNING"},
            "kombu": {"level": "WARNING"},
            "python_multipart": {"level": "WARNING"},
            "httpcore": {"level": "WARNING"},
            "watchdog": {"level": "WARNING"},
            # add more here as needed
        },
    }

def setup_logging():
    """Call this in non-Celery contexts (FastAPI, scripts, etc.)."""
    dictConfig(LOG_CONFIG)

# Celery workers hijack the root logger, so we re-apply our config when they start:
@after_setup_logger.connect
@after_setup_task_logger.connect
def _configure_celery_logger(logger, *args, **kwargs) -> None:
    """This function is called when the Celery logger is set up. It configures the logger to use the same configuration as the rest of the application in the background."""
    dictConfig(LOG_CONFIG)