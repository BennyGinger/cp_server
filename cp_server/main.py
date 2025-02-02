from fastapi import FastAPI

from .redis_server.redis_server import start_redis
from .celery_server.celery_server import start_celery_worker
from .endpoints.app_utils import router as app_utils_router
from .endpoints.mount import mount_dirs

from . import logger
from .utils import RedisServerError, CeleryServerError


app = FastAPI()

app.state.src_dir = None
app.state.dst_dir = None

# Start Redis and Celery when the app starts
logger.info("Checking Redis and Celery services...")
try:
    start_redis()
    start_celery_worker()
except RedisServerError as e:
    logger.error(f"Error starting Redis: {e}")
except CeleryServerError as e:
    logger.error(f"Error starting Celery: {e}")


app.include_router(app_utils_router)
app.include_router(mount_dirs)



