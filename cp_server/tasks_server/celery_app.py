import os

from kombu.serialization import register
from celery import Celery

from cp_server.tasks_server import get_logger
from cp_server.tasks_server.utils.serialization_utils import custom_encoder, custom_decoder


CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_BACKEND_URL = os.getenv("CELERY_BACKEND_URL", "redis://localhost")


# Set up logging for the Celery app
logger = get_logger('celery_app')
logger.info("Initializing Celery app...")

# Register the custom serializer
register('custom_ndarray',        
    encoder=custom_encoder,  
    decoder=custom_decoder,  
    content_type='application/x-custom-ndarray',
    content_encoding='utf-8')

def create_celery_app(include_tasks: bool = False) -> Celery:
    """
    Create and configure a Celery application instance. It is meant to be used as a singleton.
    This function sets up the Celery app with the specified broker and backend URLs, and registers a custom serializer for handling numpy arrays.
    It can also include the tasks module if specified, when running as a worker.
    Args:
        include_tasks (bool): If True, include the tasks module in the Celery app.
    Returns:
        Celery: Configured Celery application instance.
    """
    # Instantiate Celery
    celery_app = Celery(
        "cp_server-tasks",
        broker=CELERY_BROKER_URL,
        backend=CELERY_BACKEND_URL,
        broker_connection_retry_on_startup=True)
    
    # Update Celery configuration
    celery_app.conf.update(
        task_serializer='custom_ndarray',
        result_serializer='custom_ndarray',
        accept_content=['application/x-custom-ndarray'],)
    
    # Only load tasks if we're running as a worker
    if include_tasks:
        celery_app.conf.update(include=["cp_server.tasks_server.tasks.celery_main_task"],)
        celery_app.conf.task_default_queue = "celery"
        celery_app.conf.task_routes = {"cp_server.tasks_server.tasks.segementation.seg_task.segment": {"queue": "gpu_tasks"}}
    return celery_app

celery_app = create_celery_app(include_tasks=True)
logger.info("Celery app initialized successfully.")