from fastapi import FastAPI

from cp_server.fastapi_app.endpoints.health import router as app_utils_router
from cp_server.fastapi_app.endpoints.process_tasks import router as segment_task
from cp_server.tasks_server.celery_app import create_celery_app
from cp_server.logging import get_logger


# Setup logging

logger = get_logger()

# Create the FastAPI app
app = FastAPI()

# Set the logger
logger.info("-----------------------------------------------")
logger.info("Starting the Cellpose server...")

# Initiate a minimal celery app, to send tasks to the celery worker
logger.info("Initiating the file watcher manager...")
min_celery_app = create_celery_app()
app.state.celery_app = min_celery_app

# Include the routers
app.include_router(app_utils_router)
app.include_router(segment_task)



