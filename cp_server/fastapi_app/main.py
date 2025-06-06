from fastapi import FastAPI

from cp_server.fastapi_app import get_logger
from cp_server.fastapi_app.endpoints.health import router as app_utils_router
from cp_server.fastapi_app.endpoints.maintenance import router as maintenance_router
from cp_server.fastapi_app.endpoints.process_tasks import router as segment_task


# Setup logging
logger = get_logger("startup")
logger.info("-----------------------------------------------")
logger.info("Initializing the Cellpose server...")

# Create the FastAPI app
app = FastAPI()

# Include the routers
app.include_router(app_utils_router)
app.include_router(maintenance_router)
app.include_router(segment_task)

# Initiate a minimal celery app, to send tasks to the celery worker
logger.info("Creating a minimal Celery app to send tasks to the worker...")
logger.debug("just to test log levels")
# Lazy import to trigger the creation of the Celery app after the fastapi app is created
from cp_server.tasks_server.celery_app import create_celery_app
min_celery_app = create_celery_app()
app.state.celery_app = min_celery_app

logger.info("Cellpose server up and running!")


