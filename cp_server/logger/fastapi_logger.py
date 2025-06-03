import logging
import os
from pathlib import Path


HOST_LOG_FOLDER = Path("/logs") # TODO: Create that folder in the Dockerfile and gets the permissions right
LOGFILE_NAME = os.getenv("LOGFILE_NAME", "fastapi_combined.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

def configure_fastapi_logger():
    """
    Configure the root logger (and/or a specific named logger) so that:
      - FastAPI’s own logs go to stdout (Uvicorn already does this by default)
      - AND to /app/logs/fastapi_combined.log (a mounted file).
    """
    logfile = HOST_LOG_FOLDER.joinpath(LOGFILE_NAME)

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
    if logging.FileHandler not in handlers:
        fh = logging.FileHandler(logfile)
        fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        fh.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        root.addHandler(fh)

