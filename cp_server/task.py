import logging

from celery import Celery
from celery.signals import after_setup_logger



logger = logging.getLogger(__name__)

app = Celery('task', broker="redis://localhost:6379/0",
             backend="redis://localhost",broker_connection_retry_on_startup=True)

@after_setup_logger.connect
def setup_loggers(logger: logging.Logger, *args, **kwargs)-> None:
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # FileHandler
    fh = logging.FileHandler("/media/ben/Analysis/Python/cp_server/logs/celery.log")
    fh.setFormatter(formatter)
    logger.addHandler(fh)



@app.task
def add(x, y):
    logger.info(f"Adding {x} and {y}")
    return x + y