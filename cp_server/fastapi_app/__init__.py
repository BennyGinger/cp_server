# Configure logging
import logging
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
BASE_DIR = find_project_root(Path(__file__).resolve())
LOGS_DIR = BASE_DIR.joinpath("logs")  # Append "logs" folder

LOGS_DIR.mkdir(parents=True, exist_ok=True)  # Create logs directory if it doesn't exist

LOG_FILE = LOGS_DIR.joinpath("app.log")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set the minimum logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log message format
    handlers=[
        logging.FileHandler(LOG_FILE),  # Save logs to a file at project root
        logging.StreamHandler(),  # Also output logs to the console
    ]
)

# Set Numba logging level to WARNING to suppress debug messages
logging.getLogger("numba").setLevel(logging.WARNING)
logging.getLogger("python_multipart").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("celery").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)