import subprocess
import time

from celery.exceptions import OperationalError

from cp_server import logger
from cp_server.task_server.celery_app import celery_app
from cp_server.utils import CeleryServerError


class CeleryWorkerManager():
    def __init__(self):
        self.worker = None
    
    def is_celery_running(self)-> bool:
        """Test if the Celery worker is running."""
        try:
            # Ping workers to check if they are running
            response = celery_app.control.ping(timeout=1)  
            return bool(response) 
        except OperationalError as o:
            logger.error(f"Celery operational error: {o}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while checking Celery status: {e}")
            return False
    
    def start_worker(self, timeout: int=120, interval: int=2)-> None:
        """Start Celery worker in a separate process if it's not already running, with a timeout."""
        
        if not self.is_celery_running():
            logger.info("Starting Celery worker ...")
            self.worker = subprocess.Popen(
                ["celery", "-A", "seg_server.task_server.celery_task", "worker", "--loglevel=info"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            
            self._wait_for_startup(timeout, interval)
        else:
            logger.info("Celery worker is already running.")

    def _wait_for_startup(self, timeout: int, interval: int)-> None:
        elapsed_time = 0
        while not self.is_celery_running() and elapsed_time < timeout:
            time.sleep(interval)
            elapsed_time += interval
            logger.info(f"Waiting for Celery to start... {elapsed_time}s elapsed")
        
        if self.is_celery_running():
            logger.info("Celery worker is now running.")
        else:
            logger.error("Celery worker did not start within the timeout period.")
            self._terminate_worker()
            raise CeleryServerError("Celery worker did not start within the timeout period.")

    def _terminate_worker(self) -> None:
        """Terminate the worker process safely."""
        if self.worker:
            try:
                self.worker.terminate()
                self.worker.wait(timeout=10)
            except Exception as e:
                logger.error(f"Error terminating the worker: {e}")
            finally:
                self.worker = None
    
    def stop_worker(self)-> None:
        """Stop the Celery worker process."""
        
        if self.worker:
            logger.info("Stopping tracked Celery worker...")
            try:
                self.worker.terminate()
                self.worker.wait(timeout=10)
            except Exception as e:
                logger.error(f"Error terminating the worker: {e}")
            finally:
                self.worker = None
            logger.info("Celery worker has been stopped.")
        else:
            logger.info("No tracked Celery worker found.")

    # Allow use as a context manager
    def __enter__(self):
        self.start_worker()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_worker()
