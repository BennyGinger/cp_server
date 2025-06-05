import logging
import os
from pathlib import Path


# Define the log file path
HOST_LOG_FOLDER = Path("/logs")
LOGFILE_NAME = os.getenv("LOGFILE_NAME", "combined_server.log")
LOG_FILE = HOST_LOG_FOLDER.joinpath(LOGFILE_NAME)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
SERVICE_NAME = os.getenv("SERVICE_NAME", "cp_server")

def _configure_logger() -> None:
    # Configure logging
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE),  # Save logs to a file at project root
            logging.StreamHandler(),])  # Also output logs to the console
        
    # Suppress specific loggers that are too verbose
    logging.getLogger("numba").setLevel(logging.WARNING)
    logging.getLogger("python_multipart").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.WARNING)
    logging.getLogger("watchdog").setLevel(logging.WARNING)
    logging.getLogger("watchdog.observers").setLevel(logging.WARNING)


def get_fastapi_logger(name: str = None) -> logging.Logger:
    """
    Get a logger with the specified name, or the root logger if no name is provided.
    The logger will be configured to log to both stdout and a file on a mounted volume.
    """
    _configure_logger()  # Ensure logging is set up before returning the logger
    base = SERVICE_NAME
    return logging.getLogger(f"{base}.{name}") if name else logging.getLogger(base)
