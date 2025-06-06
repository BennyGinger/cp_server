import logging
from pathlib import Path
import subprocess
import shutil
import threading

from cp_server.utils.env_managment import propagate_env_vars

# Can't use `get_logger` from gem_screening.logger because there is no SERVICE_NAME defined in this module. Fallback to basic logging setup.
logger = logging.getLogger("cp_server.compose_manager")

# 'Grab' the env vars if any, and propagate them to the .env file
ROOT = Path(__file__).parent.parent.resolve()
propagate_env_vars(ROOT)

def _get_base_cmd() -> list[str]:
    """
    Get the base command for Docker Compose.
    This function checks for the `docker-compose` or `docker compose` command
    and returns the command with the path to the Docker Compose file.
    """
    compose_file = ROOT.joinpath("docker-compose.yml")
    compose_cmd = shutil.which("docker-compose") or shutil.which("docker compose")
    return [compose_cmd, "-f", str(compose_file)]

def compose_down() -> None:
    """
    Tear down the Docker Compose environment.
    This function will stop and remove all containers defined in the Docker Compose file.
    """
    logger.info("Tearing down Docker Compose…")
    base_cmd = _get_base_cmd()
    subprocess.run([*base_cmd, "down"], check=False)
    logger.info("Compose is down.")

def _stream_compose_logs():
    base_cmd = _get_base_cmd()
    cmd = [*base_cmd, "logs", "-f"]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    for raw in proc.stdout:
        line = raw.rstrip()
        if 'fastapi' in line:
            # Skip fastapi logs, they are not relevant for the pipeline
            continue
        # 1) Show on pipeline’s console:
        print(line)
        # 2) Also write into the pipeline’s logfile:
        logger = logging.getLogger("compose_manager")
        logger.info(line)
    proc.wait()
    

def compose_up(stream_log: bool = False) -> None:
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
                           Default is False, which means logs will not be streamed.
    Example:
    ```python
    from cp_server import ComposeManager
    # Use the context manager to manage Docker Compose lifecycle
    with ComposeManager(stream_log=True):
        # Your code here
        pass
    ```
    """
    def __init__(self, stream_log: bool = False) -> None:
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