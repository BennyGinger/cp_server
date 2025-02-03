# Configure Celery logging
import logging
from celery.signals import after_setup_logger

from seg_server.utils import find_project_root

celery_logger = logging.getLogger(__name__)

@after_setup_logger.connect
def setup_loggers(logger: logging.Logger, *args, **kwargs)-> None:
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    log_path = find_project_root().joinpath("logs","celery.log")
    
    # FileHandler
    fh = logging.FileHandler("/media/ben/Analysis/Python/cp_server/logs/celery.log")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # StreamHandler
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    # Set the logging level
    logger.setLevel(logging.DEBUG)
    
    # Disable Module logging
    celery_mod_logger = logging.getLogger("celery")
    celery_mod_logger.disabled = True
    kombu_logger = logging.getLogger('kombu')
    kombu_logger.setLevel(logging.WARNING)
    
    # Append an empty line at the beginning of the log file
    with open(log_path, "a") as f:
        f.write("\n")