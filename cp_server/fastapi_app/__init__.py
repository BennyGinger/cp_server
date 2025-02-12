# Configure logging
import logging

from cp_server import LOGS_DIR


# Define the log file path
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
celery_mod_logger = logging.getLogger("celery")
celery_mod_logger.disabled = True

logger = logging.getLogger(__name__)