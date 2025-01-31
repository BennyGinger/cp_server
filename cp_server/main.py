# Third-party imports
from fastapi import FastAPI
import uvicorn
# Local imports
from .redis_utils import start_redis
from .celery_worker import start_celery_worker
from . import logger  # Import global logger


app = FastAPI()

# Start Redis and Celery when the app starts
logger.info("Checking Redis and Celery services...")
start_redis()
start_celery_worker()

@app.get("/")
def read_root():
    return {"message": "FastAPI server is running with Celery and Redis"}

if __name__ == "__main__":
    logger.info("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)