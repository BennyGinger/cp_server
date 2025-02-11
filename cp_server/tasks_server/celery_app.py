import os

from celery import Celery


CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_BACKEND_URL = os.getenv("CELERY_BACKEND_URL", "redis://localhost")


def create_celery_app(include_tasks: bool = False)-> Celery:
    app = Celery(
        "cp_server-tasks",
        broker=CELERY_BROKER_URL,
        backend=CELERY_BACKEND_URL,
        broker_connection_retry_on_startup=True)
    
    # Only load tasks if we're running as a worker
    if include_tasks:
        app.conf.update(include=["cp_server.tasks_server.celery_tasks"])
    return app


celery_app = create_celery_app(include_tasks=True)
