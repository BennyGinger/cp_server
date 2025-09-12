# cp_server/utils/env_managment.py
import os
import sys
from pathlib import Path

from dotenv import load_dotenv, dotenv_values

from cp_server.utils.paths import get_root_path


LOGFILE_NAME = os.getenv("LOGFILE_NAME", "task_servers.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
BASE_URL = os.getenv("BASE_URL", "localhost")
TZ = os.getenv("TZ", "Europe/Berlin")

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
LOGFILE_NAME=task_servers.log

#----------- TIMEZONE CONFIGURATION -----------
# Timezone for Docker containers to match host system
TZ=Europe/Berlin
"""


def _get_current_uid_gid(default_uid=1000, default_gid=1000):
    if sys.platform.startswith("win"):
        # Windows doesn’t have POSIX uids; use defaults or read from env
        return default_uid, default_gid
    else:
        try:
            return os.getuid(), os.getgid() # type: ignore
        except AttributeError:
            # If os.getuid() or os.getgid() are not available (e.g., on some platforms)
            # we fall back to the defaults.
            return default_uid, default_gid

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
    
    # If the .env file does not exist, create it with a template
    if not env_path.exists():
        env_path.write_text(TEMPLATE)
    else:
        # Load existing .env into the environment (without overriding real env)
        # so os.getenv can see values from the file when not set in the OS.
        load_dotenv(env_path, override=False)
    
    # Ensure the .env file is writable
    if not os.access(env_path.parent, os.W_OK):
        raise PermissionError(f"Cannot write to {env_path!r}")
    
    # Compute uid/gid
    uid, gid = _get_current_uid_gid()

    # Load existing .env key-values using dotenv parser (handles quotes, etc.)
    lines: dict[str, str] = {}
    try:
        lines = {k: str(v) for k, v in dotenv_values(env_path).items()}  # type: ignore[arg-type]
    except Exception:
        # Fallback to naive parsing if dotenv fails for any reason
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            key, _, val = line.partition("=")
            lines[key.strip()] = val.strip()

    # Override your USER_UID / USER_GID
    lines["USER_UID"] = str(uid)
    lines["USER_GID"] = str(gid)
    
    # Merge LOG/URL settings: prefer OS env, then existing .env, then defaults
    logfile_name = os.getenv("LOGFILE_NAME") or lines.get("LOGFILE_NAME") or LOGFILE_NAME
    log_level = (os.getenv("LOG_LEVEL") or lines.get("LOG_LEVEL") or LOG_LEVEL).upper()
    base_url = os.getenv("BASE_URL") or lines.get("BASE_URL") or BASE_URL
    tz = os.getenv("TZ") or lines.get("TZ") or TZ
    lines["LOGFILE_NAME"] = logfile_name
    lines["LOG_LEVEL"] = log_level
    lines["BASE_URL"] = base_url
    lines["TZ"] = tz
    
    # Add the HOST_DIR: prefer OS env, then from existing .env
    host_dir = os.getenv("HOST_DIR") or lines.get("HOST_DIR")
    if not host_dir:
        raise ValueError("HOST_DIR must be set (in the environment or .env) to the directory you want to mount in the Docker containers.")
    lines["HOST_DIR"] = host_dir
    
    # Write back (atomically). On Windows, .replace() overwrites the target.
    tmp_path = env_path.with_suffix(".tmp")
    content = "\n".join(f"{k}={v}" for k, v in lines.items()) + "\n"
    try:
        tmp_path.unlink(missing_ok=True)
    except Exception:
        pass
    tmp_path.write_text(content, encoding="utf-8")
    try:
        tmp_path.replace(env_path)
    except OSError:
        try:
            env_path.unlink(missing_ok=True)
        except Exception:
            pass
        tmp_path.rename(env_path)
    
    # Load the updated .env file into the environment
    load_dotenv(env_path, override=True)

