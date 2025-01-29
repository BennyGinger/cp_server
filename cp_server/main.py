from fastapi import FastAPI, HTTPException
import uvicorn
from pathlib import Path
from .tasks import process_images
from . import logger  # Import global logger

app = FastAPI()

# Configuration dictionary to store active tasks
tasks = {}

@app.post("/start_task")
def start_task(src_dir: str, dst_dir: str, image_name: str, settings: dict)-> dict:
    """Start a new segmentation task for a single image"""
    if not Path(src_dir) or not Path(dst_dir):
        logger.error("Source or destination directory does not exist")
        raise HTTPException(status_code=400, detail="Source or destination directory does not exist")
    
    tasks[image_name] = "running"
    logger.info(f"Starting task for {image_name}")
    
    # Run processing in Celery
    process_images.apply_async(args=[src_dir, dst_dir, settings, image_name])
    
    return {"task_id": image_name, "status": "started"}

@app.get("/task_status/{image_name}")
def task_status(image_name: str)-> dict:
    """Check the status of a task"""
    status = tasks.get(image_name, "not found")
    logger.info(f"Checking status for {image_name}: {status}")
    return {"task_id": image_name, "status": status}


if __name__ == "__main__":
    logger.info("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)