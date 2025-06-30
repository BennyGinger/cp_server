# cp_server/utils/env_managment.py
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from cp_server.utils.paths import get_root_path


LOGFILE_NAME = os.getenv("LOGFILE_NAME", "combined_server.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
BASE_URL = os.getenv("BASE_URL", "localhost")

TEMPLATE = """\
BASE_URL="localhost"

# You can leave these as-is for most setups:
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_BACKEND_URL=redis://redis:6379/1

# Redis configuration for logging:
REDIS_HOST=redis
REDIS_PORT=6379
# Use DB=2 so that Celery's DB=0 (broker) and DB=1 (results) stay separate:
REDIS_DB=2

# These will be filled in by the script:
USER_UID=1000
USER_GID=1000

#----------- LOGGING CONFIGURATION -----------
# Control logging verbosity: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO
LOGFILE_NAME=combined_server.log
"""


def _get_current_uid_gid(default_uid=1000, default_gid=1000):
    if sys.platform.startswith("win"):
        # Windows doesn’t have POSIX uids; use defaults or read from env
        return default_uid, default_gid
    else:
        return os.getuid(), os.getgid()

def sync_dotenv() -> None:
    """
    Ensure the .env file exists and is writable, then propagate environment variables
    from the current environment to the .env file.
    This function will:
        - Create a .env file with a template if it does not exist.
        - Ensure the .env file is writable.
        - Read existing variables from the .env file, if any.
        - Sets HOST_DIR to be mounted in the Docker containers.
        - Override BASE_URL with the current value or default.
        - Override USER_UID and USER_GID with the current user's UID and GID.
        - Override LOGFILE_NAME and LOG_LEVEL with values from the environment or defaults.
        - Write the updated variables back to the .env file.
    This will ensure that each docker container has the correct user and logging configurations for the current user running the script.
    
    Raises:
        PermissionError: If the .env file is not writable.
        ValueError: If HOST_DIR is not set in the environment.
    """
    # Ensure the .env file exists
    root = get_root_path()
    env_path = root.joinpath(".env")
    
    # Ensure the .env file is writable
    if not os.access(env_path, os.W_OK):
        raise PermissionError(f"Cannot write to {env_path!r}")
    
    # If the .env file does not exist, create it with a template
    if not env_path.exists():
        env_path.write_text(TEMPLATE)
    
    # Compute uid/gid
    uid, gid = _get_current_uid_gid()

    # Load existing .env (if any)
    lines = {}
    for line in env_path.read_text().splitlines():
        if not line.strip() or line.startswith("#"): 
            continue
        key, _, val = line.partition("=")
        lines[key] = val

    # Override your USER_UID / USER_GID
    lines["USER_UID"] = str(uid)
    lines["USER_GID"] = str(gid)
    
    # Override the LOGS setups
    lines["LOGFILE_NAME"] = LOGFILE_NAME
    lines["LOG_LEVEL"] = LOG_LEVEL
    
    # Override the BASE_URL
    lines["BASE_URL"] = BASE_URL
    
    # Add the HOST_DIR: ⚠️ MUST BE PROVIDED BY THE USER ⚠️ 
    host_dir = os.getenv("HOST_DIR", None)
    if host_dir is None:
        raise ValueError("HOST_DIR environment variable must be set to the directory you want to mount in the Docker containers.")
    lines["HOST_DIR"] = host_dir
    
    # Write back
    tmp_path = env_path.with_suffix(".tmp")
    content = "\n".join(f"{k}={v}" for k, v in lines.items()) + "\n"
    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.rename(env_path)  # atomic rename
    
    # Load the updated .env file into the environment
    load_dotenv(env_path, override=True)

