# Configure logging
import logging
from pathlib import Path

# Ensure logs directory exists at the project root
BASE_DIR = Path(__file__).resolve().parent.parent  # Moves two levels up to project root
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