from fastapi import FastAPI

from cp_server.broker_service.redis_server import start_redis
from cp_server.task_server.worker_managment import CeleryWorkerManager
from cp_server.endpoints.app_utils import router as app_utils_router
from cp_server.endpoints.mount import router as mount_dirs
from cp_server.endpoints.segment import router as segment_task

from cp_server import logger
from cp_server.utils import RedisServerError, CeleryServerError


app = FastAPI()

app.state.src_dir = None
app.state.dst_dir = None

# Start Redis and Celery when the app starts
logger.info("-----------------------------------------------")
logger.info("Starting the Cellpose server...")
logger.info("Checking Redis and Celery services...")
try:
    start_redis()
    CeleryWorkerManager().start_worker()
except RedisServerError as e:
    logger.error(f"Error starting Redis: {e}")
except CeleryServerError as e:
    logger.error(f"Error starting Celery: {e}")


app.include_router(app_utils_router)
app.include_router(mount_dirs)
app.include_router(segment_task)



