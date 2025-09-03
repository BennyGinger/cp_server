import logging
import os
from pathlib import Path
import re
import subprocess
import shutil
import threading
import time
import requests

from cp_server.utils.env_managment import sync_dotenv, BASE_URL, LOGFILE_NAME
from cp_server.utils.paths import get_root_path

# Can't use `get_logger` from gem_screening.logger because there is no SERVICE_NAME defined in this module. Fallback to basic logging setup.
logger = logging.getLogger("cp_server.compose_manager")

# 'Grab' the env vars if any, and propagate them to the .env file
sync_dotenv()
FASTAPI_URL = f"http://{BASE_URL}:8000"
host_dir = os.getenv("HOST_DIR", ".")
HOST_LOG_FOLDER = Path(host_dir).joinpath("logs")
if not HOST_LOG_FOLDER.exists():
    HOST_LOG_FOLDER.mkdir(parents=True, exist_ok=True)

def _get_base_cmd() -> list[str]:
    """
    Get the base command for Docker Compose.
    This function checks for the `docker-compose` or `docker compose` command
    and returns the command with the path to the Docker Compose file.
    """
    root = get_root_path()
    compose_file = root.joinpath("docker-compose.yml")
    # Try docker-compose v1 first
    v1 = shutil.which("docker-compose")
    if v1:
        return [v1, "-f", str(compose_file)]
    # Fall back to docker compose v2
    docker = shutil.which("docker")
    if docker:
        return [docker, "compose", "-f", str(compose_file)]
    # Raise an error if neither command is found
    raise RuntimeError("Neither 'docker-compose' nor 'docker' (with compose) found in PATH")

def compose_down() -> None:
    """
    Tear down the Docker Compose environment.
    This function will stop and remove all containers defined in the Docker Compose file.
    """
    logger.info("Tearing down Docker Compose…")
    base_cmd = _get_base_cmd()
    subprocess.run([*base_cmd, "down"], check=False)
    logger.info("Compose is down.")

def _stream_compose_logs() -> None:
    """
    Stream the logs of the Docker Compose services.
    This function will run `docker-compose logs -f` and write the logs to a file
    while also printing them to the console.
    It will create a log file in the HOST_LOG_FOLDER with the name LOGFILE_NAME.
    """
    base_cmd = _get_base_cmd()
    log_path = HOST_LOG_FOLDER.joinpath(LOGFILE_NAME)
    proc = subprocess.Popen(
        [*base_cmd, "logs", "-f"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    
    # Pattern to match progress bar lines (percentage, bar, size info)
    progress_pattern = re.compile(r'^\s*\d+%\|.*?\|\s*[\d.]+[kMG]?/?[\d.]+[kMG]?\s*\[.*?\]')
    last_progress_line = None
    
    with log_path.open("a", encoding="utf-8") as f:
        assert proc.stdout is not None, "Failed to capture logs: stdout is None"
        for line in proc.stdout:
            # Check if this is a progress bar line
            if progress_pattern.search(line.strip()):
                # Only print/log if it's different from the last progress line
                # or if it's a completion (100%)
                if (last_progress_line != line.strip() and 
                    (line.strip() != last_progress_line or "100%" in line)):
                    # Keep progress feedback visible locally
                    print(line, end="")
                    f.write(line)
                    f.flush()
                    last_progress_line = line.strip()
            else:
                # Non-progress lines from remote services: write to file only
                f.write(line)
                f.flush()
                last_progress_line = None  # Reset progress tracking
    proc.wait()

def _wait_for_services(timeout: int = 120, interval: int = 1) -> None:
    """Poll your health endpoints until they all return 200 or timeout."""
    endpoints = [
        "/health/redis",
        "/health",
        "/health/celery",
    ]
    
    # Give services time to start up before first health check
    initial_delay = 5.0  # seconds
    logger.info(f"Waiting for services to start up before health checks...")
    time.sleep(initial_delay)
    
    start = time.time()
    while time.time() - start < timeout:
        all_ok = True
        failed_endpoints = []
        for url in endpoints:
            try:
                r = requests.get(f"{FASTAPI_URL}{url}", timeout=1)
                if r.status_code != 200:
                    failed_endpoints.append(f"{url} (status: {r.status_code})")
                    all_ok = False
            except requests.RequestException as e:
                failed_endpoints.append(f"{url} (error: {e})")
                all_ok = False
        
        if all_ok:
            logger.info("All services healthy.")
            return
        
        # Log which endpoints are failing every 10 seconds
        elapsed = time.time() - start
        if int(elapsed) % 10 == 0:
            logger.info(f"All Services still not healthy: {', '.join(failed_endpoints)}")
        
        time.sleep(interval)
    raise RuntimeError(f"Services are not healthy after {timeout}s. Failed endpoints: {', '.join(failed_endpoints)}")

def compose_up(stream_log: bool) -> None:
    """
    Bring up the Docker Compose environment.
    This function will tear down any stale state first and then bring up the Docker Compose services.
    If the `docker-compose` command is not found, it will raise an error.
    """
    logger.info("Bringing up Docker Compose…")
    
    # always tear down stale state first
    compose_down()
    
    base_cmd = _get_base_cmd()
    try:
        subprocess.run([*base_cmd, "up", "-d", "--remove-orphans"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error("Compose up failed (exit code %s)", e.returncode)
        raise
    
    _wait_for_services()
    
    if stream_log:
        # Start a daemon thread that follows `docker-compose logs -f`
        t = threading.Thread(target=_stream_compose_logs, daemon=True)
        t.start()
        logger.info("Compose is up. Now streaming logs…")
        return
    logger.info("Compose is up.")

class ComposeManager:
    """
    Context manager for managing Docker Compose lifecycle.
    This class provides a convenient way to bring up and tear down Docker Compose services
    using a context manager.
    If provided, it will stream the logs of the Docker Compose services.
    
    Args:
        stream_log (bool): If True, stream the logs of the Docker Compose services.
                           Default is True.
    Examples:
    ```python
    from cp_server import ComposeManager
    # Use the context manager to manage Docker Compose lifecycle
    with ComposeManager(stream_log=True):
        # Your code here
        ...
    ```
    """
    def __init__(self, stream_log: bool = True) -> None:
        self.stream_log = stream_log
    
    def __enter__(self) -> None:
        """
        Enter the runtime context related to this object.
        This method is called when entering the context manager.
        It brings up the Docker Compose environment.
        """
        compose_up(self.stream_log)

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """
        Exit the runtime context related to this object.
        This method is called when exiting the context manager.
        It tears down the Docker Compose environment.
        """
        compose_down()