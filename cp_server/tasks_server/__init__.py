# Configure Celery logging
import logging
from celery.signals import after_setup_logger

from cp_server import LOGS_DIR


celery_logger = logging.getLogger(__name__)

# Define the log file path
LOG_FILE = LOGS_DIR.joinpath("app.log")

@after_setup_logger.connect
def setup_loggers(logger: logging.Logger, *args, **kwargs)-> None:
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # FileHandler
    fh = logging.FileHandler(LOG_FILE)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # StreamHandler
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    # Set the logging level
    logger.setLevel(logging.DEBUG)
    
    # Disable Module logging
    logging.getLogger("celery.bootsteps").setLevel(logging.WARNING)
    logging.getLogger("kombu").setLevel(logging.WARNING)