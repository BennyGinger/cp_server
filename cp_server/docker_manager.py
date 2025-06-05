import subprocess
import shutil

# Ensure that the env file exists
from cp_server.config import ROOT
from cp_server.utils.env_managment import propagate_env_vars
propagate_env_vars(ROOT)

# Setup logging
from cp_server.logger.base_log import get_logger
logger = get_logger("compose_manager")


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

def compose_up() -> None:
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