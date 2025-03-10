from pathlib import Path


def find_project_root(current_path: Path) -> Path:
    """
    Recursively search for the project root directory by looking for the .git directory.
    """
    for parent in current_path.parents:
        if parent.joinpath(".git").exists():
            return parent
    raise FileNotFoundError("Project root with .git directory not found.")

# Ensure logs directory exists at the project root
ROOT_DIR = find_project_root(Path(__file__).resolve())

# Append "logs" folder to the project root
LOGS_DIR = ROOT_DIR.joinpath("logs")  
LOGS_DIR.mkdir(parents=True, exist_ok=True)