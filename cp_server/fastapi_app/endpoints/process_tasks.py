from typing import Any
from fastapi import APIRouter, Request, HTTPException
from celery import Celery

from cp_server.fastapi_app.endpoints.utils import ProcessRequest, BackgroundRequest
from cp_server.fastapi_app import get_logger
from cp_server.tasks_server.utils.redis_com import redis_client


# Setup logging
logger = get_logger(__name__)

# Create a router for the segment task
router = APIRouter()


@router.post("/process")
def process_images_endpoint(request: Request, payload: ProcessRequest) -> dict[str, Any]:
    """
    Endpoint to process images using the provided payload.
    This endpoint accepts a payload containing:
    - `mod_settings`: Settings for the model.
    - `cp_settings`: Settings for the Cellpose processing.
    - `img_path`: A string path to an image file, a directory containing images, or a list of image paths (str).
    - `dst_folder`: Destination folder where processed images will be saved.
    - `round`: The round number for processing.
    - `run_id`: Unique identifier for the processing run.
    - `total_fovs`: Optional total number of fields of view.
    - `do_denoise`: Whether to apply denoising (default is True).
    - `track_stitch_threshold`: Threshold for stitching masks during tracking (default is 0.75).
    - `sigma`: Sigma value for background subtraction (default is 0.0).
    - `size`: Size parameter for background subtraction (default is 7).
    This endpoint will send tasks to a Celery worker to process the images.
    It returns a dictionary with the task IDs and the count of tasks sent.
    
    :param request: The FastAPI request object.
    :param payload: The payload containing the image processing parameters.
    
    :return: A dictionary with task IDs and count of tasks sent.
    
"""
    # Get the source and destination directories
    celery_app: Celery = request.app.state.celery_app
    
    # Initialize the counter for pending tracks
    if payload.round == 2:
        redis_client.setnx(f"pending_tracks:{payload.run_id}", payload.total_fovs)
        redis_client.expire(f"pending_tracks:{payload.run_id}", 24 * 3600)
    
    logger.info(f"Enqueuing {len(payload.image_paths)} images for processing (round={payload.round})")
    
    # Process the paths
    task_ids = []
    for path in payload.image_paths:
        params = payload.model_dump()
        params["img_file"] = path
        task = celery_app.send_task(
            "cp_server.tasks_server.tasks.celery_main_task.process_images",
            kwargs=params)
        task_ids.append(task.id)

    return {"run_id": payload.run_id, "task_ids": task_ids, "count": len(task_ids)}

@router.post("/process_bg_sub")
def process_bg_sub_endpoint(request: Request, payload: BackgroundRequest) -> dict[str, Any]:
    """
    Endpoint to process background subtraction for images.
    This endpoint accepts a payload containing:
    - `img_path`: A string path to an image file, a directory containing images, or a list of image paths (str).
    - `sigma`: Sigma value for background subtraction (default is 0.0).
    - `size`: Size parameter for background subtraction (default is 7).
    
    This endpoint will send tasks to a Celery worker to process the images.
    It returns a dictionary with the task IDs and the count of tasks sent.
    
    :param request: The FastAPI request object.
    :param payload: The payload containing the background subtraction parameters.
    
    :return: A dictionary with task IDs and count of tasks sent.
    """
    celery_app: Celery = request.app.state.celery_app
    
    logger.info(f"Enqueuing {len(payload.image_paths)} images for background subtraction")
    
    # Process the paths
    task_ids = []
    for path in payload.image_paths:
        params = payload.model_dump()
        params["img_file"] = path
        task = celery_app.send_task(
            "cp_server.tasks_server.tasks.bg_sub.remove_bg",
            kwargs=params)
        task_ids.append(task.id)

    return {"task_ids": task_ids, "count": len(task_ids)}

@router.get("/process/{run_id}/status")
def get_process_status(run_id: str) -> dict:
    """
    Check remaining tracks for a given run_id.
    Returns 404 if run_id is not found in Redis.
    """
    pending_key  = f"pending_tracks:{run_id}"
    finished_key = f"finished:{run_id}"
    
    # 1) If we have a finished flag, report done
    if redis_client.exists(finished_key):
        return {"run_id": run_id, "status": "finished", "remaining": 0}
    
    # 2) If we still have a pending counter, report processing
    if redis_client.exists(pending_key):
        rem = int(redis_client.get(pending_key))
        return {"run_id": run_id, "status": "processing", "remaining": rem}
    
    # 3) Neither key exists → invalid run_id
    raise HTTPException(status_code=404,
                        detail=f"run_id '{run_id}' not found")