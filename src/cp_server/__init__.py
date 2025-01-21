# Configure logging
import logging


logging.basicConfig(
    level=logging.DEBUG,  # Set the minimum logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log message format
    handlers=[
        logging.FileHandler("logs/app.log"),  # Save logs to a file named 'app.log'
        logging.StreamHandler(),  # Also output logs to the console
    ])

# Set Numba logging level to WARNING to suppress debug messages
numba_logger = logging.getLogger('numba')
numba_logger.setLevel(logging.WARNING)
pmm_logger = logging.getLogger('python_multipart')
pmm_logger.setLevel(logging.WARNING)
