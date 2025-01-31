import os
import subprocess
import time

from celery import Celery

from .. import logger  
from ..utils import CeleryServerError


# Configure Celery
celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    broker_connection_retry_on_startup=True)

# Celery worker process
WORKER = None

def is_celery_running()-> bool:
    try:
        response = celery_app.control.ping(timeout=1)  # Ping workers
        return bool(response)  # Returns True if workers respond
    except Exception as e:
        print(f"Error: {e}")
        return False
    
def start_celery_worker()-> None:
    """Start Celery worker in a separate process if it's not already running, with a timeout."""
    global WORKER
    
    if not is_celery_running():
        logger.info("Starting Celery worker...")
        WORKER = subprocess.Popen(
            ["celery", "-A", "cp_server.celery.celery_server.celery_app", "worker", "--loglevel=info"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        
        # Wait until Celery is running, with a max timeout of 2 minutes
        timeout = 120  # 2 minutes
        interval = 2  # Check every 2 seconds
        elapsed_time = 0
        
        while not is_celery_running() and elapsed_time < timeout:
            time.sleep(interval)
            elapsed_time += interval
            logger.info(f"Waiting for Celery to start... {elapsed_time}s elapsed")
        
        if is_celery_running():
            logger.info("Celery worker is now running.")
        else:
            logger.error("Celery worker did not start within the timeout period.")
            WORKER.terminate()
            WORKER.wait()
            WORKER = None
            raise CeleryServerError("Celery worker did not start within the timeout period.")
    else:
        logger.info("Celery worker is already running.")
        return True

def stop_celery_worker()-> None:
    """Stop the Celery worker process."""
    global WORKER
    
    if is_celery_running():
        logger.info("Stopping Celery worker...")
        if WORKER:
            WORKER.terminate()  # Gracefully terminate
            WORKER.wait()  # Wait for process to exit
            WORKER = None
            logger.info("Celery worker has been stopped.")
        else:
            os.system("pkill -9 -f 'celery'")  # Fallback to force kill
            logger.info("Celery worker forcefully stopped.")
    else:
        logger.info("No Celery worker is running.")


if __name__ == "__main__":
    print(is_celery_running())
    start_celery_worker()
    print(is_celery_running())
    stop_celery_worker()
    print(is_celery_running())