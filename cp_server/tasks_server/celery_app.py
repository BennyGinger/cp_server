import os

from kombu.serialization import register
from celery import Celery
from celery.signals import worker_ready

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
        accept_content=['application/x-custom-ndarray'],
        # Reduce verbosity of task completion logging
        worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
        worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
    )
    
    # Only load tasks if we're running as a worker
    if include_tasks:
        celery_app.conf.update(include=[
            "cp_server.tasks_server.tasks.celery_main_task",
            "cp_server.tasks_server.tasks.bg_sub.bg_sub_task",
            "cp_server.tasks_server.tasks.counter.counter_task_manager",
            "cp_server.tasks_server.tasks.track.track_task",
            "cp_server.tasks_server.tasks.segementation.seg_task",
        ])
        celery_app.conf.task_default_queue = "celery"
        celery_app.conf.task_routes = {"cp_server.tasks_server.tasks.segementation.seg_task.segment": {"queue": "gpu_tasks"}}
    return celery_app

celery_app = create_celery_app(include_tasks=True)

@worker_ready.connect
def preload_models(sender, **kwargs):
    """
    Preload commonly used models when worker starts using cellpose-kit.

    Note:
        The **kwargs argument is required because Celery's signal system may pass additional
        keyword arguments to the handler. This ensures compatibility with Celery's signal API,
        even though these extra arguments are not used in this function.
    """
    # Only preload on GPU workers (they have cellpose)
    worker_name = getattr(sender, 'hostname', '')
    if 'gpu' not in worker_name.lower():
        logger.info("Skipping model preload on non-GPU worker")
        return
        
    logger.info("Preloading Cellpose models with cellpose-kit...")
    
    try:
        from cp_server.tasks_server.tasks.segementation.cp_segmentation import model_manager
        
        # Preload common model configurations
        common_configs = [
            {
                'pretrained_model': 'cyto3', 
                'gpu': True, 
                'diameter': 30,
                'do_denoise': True,
                'use_nuclear_channel': False
            },
            {
                'pretrained_model': 'cpsam', 
                'gpu': True, 
                'diameter': 40,
                'do_denoise': True,
                'use_nuclear_channel': False
            },
        ]
        
        for config in common_configs:
            try:
                model_manager.get_configured_settings(config)
                logger.info(f"Preloaded cellpose-kit model: {config}")
            except Exception as e:
                logger.warning(f"Failed to preload cellpose-kit model {config}: {e}")
        
        logger.info("Cellpose-kit model preloading complete")
    except ImportError:
        logger.info("Cellpose-kit not available on this worker - skipping model preload")
    except Exception as e:
        logger.warning(f"Cellpose-kit model preloading failed: {e}")

# Configure logging to reduce verbosity of task completion messages
import logging
trace_logger = logging.getLogger('celery.app.trace')
trace_logger.setLevel(logging.DEBUG)  # This will show task completion logs only in DEBUG mode

logger.info("Celery app initialized successfully.")