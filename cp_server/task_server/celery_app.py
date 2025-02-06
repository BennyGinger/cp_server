import os

from celery import Celery


CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_BACKEND_URL = os.getenv("CELERY_BACKEND_URL", "redis://localhost")

celery_app = Celery("tasks", 
                    broker=CELERY_BROKER_URL, 
                    backend=CELERY_BACKEND_URL, 
                    broker_connection_retry_on_startup=True)
