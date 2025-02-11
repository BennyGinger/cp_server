from fastapi import FastAPI

from cp_server.fastapi_app.endpoints.health import router as app_utils_router
from cp_server.fastapi_app.endpoints.file_watcher import router as file_watcher
from cp_server.fastapi_app.endpoints.segment import router as segment_task
from cp_server.fastapi_app.watcher.watcher_manager import FileWatcherManager
from cp_server.task_server.celery_app import celery_app
from cp_server.fastapi_app import logger


app = FastAPI()

app.state.src_dir = None
app.state.dst_dir = None

# Set the logger
logger.info("-----------------------------------------------")
logger.info("Starting the Cellpose server...")
logger.info("Checking Redis and Celery services...")

# Start the file watcher manager
logger.info("Initiating the file watcher manager...")
app.state.watcher_manager = FileWatcherManager(celery_app)

# Include the routers
app.include_router(app_utils_router)
app.include_router(file_watcher)
app.include_router(segment_task)



