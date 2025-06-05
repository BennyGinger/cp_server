import logging
import os
from pathlib import Path

from celery.signals import after_setup_logger


# Define the constants for logging
HOST_LOG_FOLDER = Path("/logs")
LOGFILE_NAME = os.getenv("LOGFILE_NAME", "combined_server.log")
LOG_FILE = HOST_LOG_FOLDER.joinpath(LOGFILE_NAME)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
SERVICE_NAME = os.getenv("SERVICE_NAME", "cp_server")

@after_setup_logger.connect
def _configure_logger(logger: logging.Logger, *args, **kwargs)-> None:
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # FileHandler
    fh = logging.FileHandler(LOG_FILE)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # StreamHandler
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    # Set the logging level
    logger.setLevel(LOG_LEVEL)
    
    # Disable Module logging
    logging.getLogger("celery").setLevel(logging.WARNING)
    logging.getLogger("celery.bootsteps").setLevel(logging.WARNING)
    logging.getLogger("celery.apps.worker").setLevel(logging.WARNING)
    logging.getLogger('kombu').setLevel(logging.WARNING)
    logging.getLogger('numba').setLevel(logging.WARNING)
    
    
def get_celery_logger(name: str = None) -> logging.Logger:
    
    """
    Get a logger with the specified name, or the root logger if no name is provided.
    The logger will be configured to log to both stdout and a file on a mounted volume.
    """
    base = SERVICE_NAME
    logger = logging.getLogger(f"{base}.{name}") if name else logging.getLogger(base)
    _configure_logger()  
    return logger