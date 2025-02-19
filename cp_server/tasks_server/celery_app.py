import os

from kombu.serialization import register
from celery import Celery

from cp_server.tasks_server.celery_app_utils import custom_encoder, custom_decoder


CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_BACKEND_URL = os.getenv("CELERY_BACKEND_URL", "redis://localhost")


# Register the custom serializer
register(
    'custom_ndarray',        
    encoder=custom_encoder,  
    decoder=custom_decoder,  
    content_type='application/x-custom-ndarray',
    content_encoding='utf-8')

def create_celery_app(include_tasks: bool = False)-> Celery:
    app = Celery(
        "cp_server-tasks",
        broker=CELERY_BROKER_URL,
        backend=CELERY_BACKEND_URL,
        broker_connection_retry_on_startup=True)
    
    # Set the custom serializer as the default
    app.conf.update(task_serializer='custom_ndarray',
                    result_serializer='custom_ndarray',
                    accept_content=['application/x-custom-ndarray'])

    # Only load tasks if we're running as a worker
    if include_tasks:
        app.conf.update(include=["cp_server.tasks_server.celery_tasks"],)
        app.conf.task_default_queue = "celery"
        app.conf.task_routes = {
            "cp_server.tasks_server.celery_tasks.segment": {"queue": "gpu_tasks"}
        }
    return app


celery_app = create_celery_app(include_tasks=True)
