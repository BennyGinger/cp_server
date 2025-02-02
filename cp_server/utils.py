import os
from pathlib import Path

class RedisServerError(Exception):
    """Raised when Redis server fails to start."""
    
class CeleryServerError(Exception):
    """Raised when Celery worker fails to start."""


def find_project_root() -> Path:
    """Find the root directory of the project."""
    current_dir = Path.cwd()
    
    while current_dir != Path("/"):
        if current_dir.joinpath('.git').exists():
            return current_dir
        current_dir = current_dir.parent
    
    raise FileNotFoundError("Project root directory not found.")

def get_app_path(file_path: str)-> str:
    """Get the path to the app from the given file path."""
    
    path = Path(file_path)
    root_dir = find_project_root()
    # Convert to relative path
    relative_path = path.relative_to(root_dir)
    app_path = str(relative_path).replace(os.sep, ".").replace(".py", "")
    return app_path

if __name__ == "__main__":
    print(get_app_path(__file__))