import subprocess
import shutil

from cp_server import ROOT
from cp_server.logger import get_logger
from cp_server.utils.env_managment import update_env_file


# Ensure the .env file is updated with the current user UID and GID
update_env_file()

# Setup logging
logger = get_logger(__name__)


COMPOSE_FILE = ROOT.joinpath("docker-compose.yml")
COMPOSE_CMD = shutil.which("docker-compose") or shutil.which("docker compose")
BASE_CMD = [COMPOSE_CMD, "-f", str(COMPOSE_FILE)]


def compose_down() -> None:
    """
    Tear down the Docker Compose environment.
    This function will stop and remove all containers defined in the Docker Compose file.
    """
    logger.info("Tearing down Docker Compose…")
    subprocess.run([*BASE_CMD, "down"], check=False)
    logger.info("Compose is down.")

def compose_up() -> None:
    """
    Bring up the Docker Compose environment.
    This function will tear down any stale state first and then bring up the Docker Compose services.
    If the `docker-compose` command is not found, it will raise an error.
    """
    logger.info("Bringing up Docker Compose…")
    
    # always tear down stale state first
    compose_down()
    try:
        subprocess.run([*BASE_CMD, "up", "-d", "--remove-orphans"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error("Compose up failed (exit code %s)", e.returncode)
        raise
    logger.info("Compose is up.")


class ComposeManager:
    """
    Context manager for managing Docker Compose lifecycle.
    This class provides a convenient way to bring up and tear down Docker Compose services
    using a context manager.
    Usage:
        with ComposeManager():
            # Your code here
            pass
    """
    def __enter__(self) -> None:
        """
        Enter the runtime context related to this object.
        This method is called when entering the context manager.
        It brings up the Docker Compose environment.
        """
        compose_up()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """
        Exit the runtime context related to this object.
        This method is called when exiting the context manager.
        It tears down the Docker Compose environment.
        """
        compose_down()