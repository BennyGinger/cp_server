from fastapi import FastAPI

from cp_server.endpoints.app_utils import router as app_utils_router
from cp_server.endpoints.mount import router as mount_dirs
from cp_server.endpoints.segment import router as segment_task
from cp_server import logger


app = FastAPI()

app.state.src_dir = None
app.state.dst_dir = None

# Start Redis and Celery when the app starts
logger.info("-----------------------------------------------")
logger.info("Starting the Cellpose server...")
logger.info("Checking Redis and Celery services...")


app.include_router(app_utils_router)
app.include_router(mount_dirs)
app.include_router(segment_task)



