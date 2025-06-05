import logging
import os
from pathlib import Path


HOST_LOG_FOLDER = os.getenv("HOST_LOG_FOLDER", "/logs")
LOGFILE_NAME = os.getenv("LOGFILE_NAME", "combined_server.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
SERVICE_NAME = os.getenv("SERVICE_NAME", "cp_server")

def _configure_logger() -> None:
    """
    Configure the root logger so that:
        - Matches the LOG_LEVEL environment variable throughout the pipeline
        - Both servers FastAPI and Celery log to the same file
    This function sets up the logging to:
        - Log to stdout (StreamHandler) so you can see logs in docker logs
        - Log to a file at /app/logs/combined_server.log (FileHandler)
    The log file is stored in the HOST_LOG_FOLDER, which should be mounted as a volume
    in the Docker container.
    The log file will be created if it does not exist, and it will append to the file
    if it does.
    The log format is set to include the timestamp, log level, logger name, and message.
    The date format is set to "YYYY-MM-DD HH:MM:SS".
    """
    logfile = Path(HOST_LOG_FOLDER).joinpath(LOGFILE_NAME)

    root = logging.getLogger()  # or use a named logger if you prefer
    root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    handlers = [type(h) for h in root.handlers]

    # 1) Ensure there's a StreamHandler (so you see FastAPI logs in docker logs)
    if logging.StreamHandler not in handlers:
        sh = logging.StreamHandler()  # defaults to stdout
        fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        sh.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        root.addHandler(sh)

    # 2) Ensure there's a FileHandler writing to /app/logs/fastapi_combined.log
    if not any(isinstance(h, logging.FileHandler) for h in root.handlers):
        fh = logging.FileHandler(logfile)
        fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        fh.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        root.addHandler(fh)
        
def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger with the specified name, or the root logger if no name is provided.
    The logger will be configured to log to both stdout and a file on a mounted volume.
    """
    _configure_logger()  # Ensure logging is set up before returning the logger
    base = SERVICE_NAME
    return logging.getLogger(f"{base}.{name}") if name else logging.getLogger(base)

