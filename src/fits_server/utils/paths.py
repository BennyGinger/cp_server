from pathlib import Path


def get_root_path() -> Path:
    """
    Get the root path for the application. It will look for the docker-compose.yml file, as it should be in the same directory.
    """
    file_path = Path(__file__).resolve()
    for path in file_path.parents:
        if path.joinpath("docker-compose.yml").exists():
            return path
    raise FileNotFoundError("Could not find docker-compose.yml in parent directories.")
