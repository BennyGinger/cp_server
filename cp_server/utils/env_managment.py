import os
import sys

from cp_server import ROOT
from cp_server.logger import get_logger


TEMPLATE = """\
# ⚠️ Please review and customize this file before running again ⚠️

# Critical, must be determined by the user:
DATA_DIR=/home/eblab/data_dir

# You can leave these as-is for most setups:
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_BACKEND_URL=redis://redis:6379/1

# These will be filled in by the script:
USER_UID=1000
USER_GID=1000
"""

logger = get_logger(__name__)

def _get_current_uid_gid(default_uid=1000, default_gid=1000):
    if sys.platform.startswith("win"):
        # Windows doesn’t have POSIX uids; use defaults or read from env
        return default_uid, default_gid
    else:
        return os.getuid(), os.getgid()

def update_env_file() -> None:
    """
    Write the current user UID and GID to the .env file.
    This function reads the existing .env file, updates the USER_UID and USER_GID,
    and writes it back.
    
    Raises:
        FileNotFoundError: If the .env file does not exist at the expected location.
        PermissionError: If the .env file is not writable.
    """
    # Ensure the .env file exists
    env_path = ROOT.joinpath(".env")
    if not env_path.exists():
        # write the template out
        env_path.write_text(TEMPLATE)
        logger.error(f"No .env found: created template at {env_path}")
        raise FileNotFoundError(
            f".env not found. A template has been created at {env_path}. "
            "Please edit DATA_DIR (and other fields) before rerunning.")
    
    # Ensure the .env file is writable
    if not os.access(env_path, os.W_OK):
        raise PermissionError(f"Cannot write to {env_path!r}")

    # 1) compute uid/gid
    uid, gid = _get_current_uid_gid()

    # 2) load existing .env (if any)
    lines = {}
    for line in env_path.read_text().splitlines():
        if not line.strip() or line.startswith("#"): 
            continue
        key, _, val = line.partition("=")
        lines[key] = val

    # 3) override your USER_UID / USER_GID
    lines["USER_UID"] = str(uid)
    lines["USER_GID"] = str(gid)
    logger.debug(f"Setting USER_UID={uid}, USER_GID={gid} in .env")

    # 4) write back
    tmp_path = env_path.with_suffix(".env.tmp")
    content = "\n".join(f"{k}={v}" for k, v in lines.items()) + "\n"
    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.rename(env_path)  # atomic rename
    logger.info(f"Updated .env with USER_UID={uid}, USER_GID={gid}")


if __name__ == "__main__":
    try:
        update_env_file()
    except Exception as e:
        print(f"Failed to write .env: {e}")
        sys.exit(1)
