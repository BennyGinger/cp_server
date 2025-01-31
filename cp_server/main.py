from fastapi import FastAPI
import uvicorn

from .redis.redis_server import start_redis, stop_redis
from .celery.celery_server import start_celery_worker, stop_celery_worker
from .celery.celery_task import process_images
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



@app.get("/")
def read_root():
    return {"message": "FastAPI server is running with Celery and Redis"}

@app.post("/stop")
def stop_services():
    """Stop Redis and Celery services."""
    stop_celery_worker()
    stop_redis()
    return {"message": "Stopped Celery and Redis services"}

@app.post("/process")
def process_images_task(src_dir: str, dst_dir: str, settings: dict, image_name: str):
    """Start a Celery task to process images with Cellpose."""
    
    logger.info(f"Received request to process {image_name}")
    
    # Update the source and destination directories
    app.state.src_dir = src_dir
    app.state.dst_dir = dst_dir
    logger.info(f"Source Path: {src_dir}")
    logger.info(f"Destination Path: {dst_dir}")
    
    task = process_images.delay(app.state.src_dir, app.state.dst_dir, settings, image_name)
    return {"task_id": task.id,
            "message": f"Processing started for {image_name}",
            "source": src_dir,
            "destination": dst_dir}

if __name__ == "__main__":
    logger.info("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)