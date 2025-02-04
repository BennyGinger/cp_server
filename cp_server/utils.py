from functools import lru_cache
from pathlib import Path

@lru_cache(maxsize=None)
def root_path() -> Path:
    """Find the root directory of the project."""
    current_dir = Path.cwd()
    
    while current_dir != Path("/"):
        if current_dir.joinpath('.git').exists():
            return current_dir
        current_dir = current_dir.parent
    
    raise FileNotFoundError("Project root directory not found.")


ROOT_PATH = root_path()


class RedisServerError(Exception):
    """Raised when Redis server fails to start."""
    
class CeleryServerError(Exception):
    """Raised when Celery worker fails to start."""

def locate_dirs(base_path: Path, folder_name: str)-> list[Path]:
    matching_dirs = []
    for subdir in base_path.rglob('*'):
        if subdir.is_dir() and subdir.name == folder_name:
            matching_dirs.append(subdir)
    return matching_dirs

