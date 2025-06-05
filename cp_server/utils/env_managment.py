# cp_server/utils/env_managment.py
import os
import sys
from pathlib import Path


TEMPLATE = """\
# ⚠️ Please review and customize this file before running again ⚠️

# Critical, must be determined by the user:
DATA_DIR=/home/eblab/data_dir

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

def propagate_env_vars(root: Path) -> None:
    """
    Ensure the .env file exists and is writable, then propagate environment variables
    from the current environment to the .env file.
    This function will:
        - Create a .env file with a template if it does not exist.
        - Ensure the .env file is writable.
        - Read existing variables from the .env file, if any.
        - Override USER_UID and USER_GID with the current user's UID and GID.
        - Override LOGFILE_NAME and LOG_LEVEL with values from the environment or defaults.
        - Write the updated variables back to the .env file.
    This will ensure that each docker container has the correct user and logging configurations
    for the current user running the script.
    
    Raises:
        FileNotFoundError: If the .env file does not exist at the expected location.
        PermissionError: If the .env file is not writable.
    """
    # Ensure the .env file exists
    env_path = root.joinpath(".env")
    if not env_path.exists():
        env_path.write_text(TEMPLATE)
        raise FileNotFoundError(
            f".env not found; template created at {env_path}. Please update it and rerun.")
    
    # Ensure the .env file is writable
    if not os.access(env_path, os.W_OK):
        raise PermissionError(f"Cannot write to {env_path!r}")

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
    lines["LOGFILE_NAME"] = os.getenv("LOGFILE_NAME", "combined_server.log")
    lines["LOG_LEVEL"] = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Write back
    tmp_path = env_path.with_suffix(".env.tmp")
    content = "\n".join(f"{k}={v}" for k, v in lines.items()) + "\n"
    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.rename(env_path)  # atomic rename


if __name__ == "__main__":
    try:
        propagate_env_vars()
    except Exception as e:
        print(f"Failed to write .env: {e}")
        sys.exit(1)
