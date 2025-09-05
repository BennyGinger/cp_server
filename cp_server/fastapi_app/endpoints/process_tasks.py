from typing import Any, cast
from pathlib import Path

from fastapi import APIRouter, Request, HTTPException
from celery import Celery

from cp_server.fastapi_app.endpoints.request_models import ProcessRequest, BackgroundRequest, RegisterMaskRequest
from cp_server.fastapi_app import get_logger
from cp_server.fastapi_app.endpoints import redis_client


# Setup logging
logger = get_logger(__name__)

# Create a router for the segment task
router = APIRouter()


@router.post("/process")
def process_images_endpoint(request: Request, payload: ProcessRequest) -> dict[str, Any]:
    """
    Endpoint to process images using the provided payload.
    This endpoint accepts a payload containing:
    - `img_path`: A string path to an image file.
    - `sigma`: Sigma value for background subtraction (default is 0.0).
    - `size`: Size parameter for background subtraction (default is 7).
    - `cellpose_settings`: Model and segmentation settings for Cellpose.
    - `dst_folder`: Destination folder where processed images will be saved.
    - `well_id`: Unique identifier for the processing well.
    - `total_fovs`: Total number of fields of view, used to set the number of pending tracks in Redis. Not included in the model dump.
    - `track_stitch_threshold`: Threshold for stitching masks during tracking. Optional, default is 0.75.
    - `round`: The round number for processing, build from the image path if not provided. Defaults to None. Not included in the model dump.
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
        redis_client.setnx(f"pending_tracks:{payload.well_id}", payload.total_fovs)
        redis_client.expire(f"pending_tracks:{payload.well_id}", 24 * 3600)
    
    logger.info(f"Sending {payload.img_path} for processing with well_id {payload.well_id}")
    
    # Process the paths
    params = payload.model_dump()
    task = celery_app.send_task(
            "cp_server.tasks_server.tasks.celery_main_task.process_images",
            kwargs=params)

    return {"well_id": payload.well_id, "task_ids": task.id}

@router.post("/process_bg_sub")
def process_bg_sub_endpoint(request: Request, payload: BackgroundRequest) -> str:
    """
    Endpoint to process background subtraction for images.
    This endpoint accepts a payload containing:
    - `img_path`: A string path to an image file.
    - `sigma`: Sigma value for background subtraction (default is 0.0).
    - `size`: Size parameter for background subtraction (default is 7).
    
    This endpoint will send tasks to a Celery worker to process the images.
    It returns a dictionary with the task IDs and the count of tasks sent.
    
    :param request: The FastAPI request object.
    :param payload: The payload containing the background subtraction parameters.
    
    :return: Task ID of the background subtraction task.
    """
    celery_app: Celery = request.app.state.celery_app
    
    logger.info(f"Sending {payload.img_path} images for background subtraction")
    
    # Process the paths
    params = payload.model_dump()
    task = celery_app.send_task(
            "cp_server.tasks_server.tasks.bg_sub.remove_bg",
            kwargs=params)

    return task.id

@router.get("/process/{well_id}/status")
async def get_process_status(well_id: str) -> dict[str, Any]:
    """
    Check remaining tracks for a given well_id.
    Returns 404 if well_id is not found in Redis.
    """
    pending_key  = f"pending_tracks:{well_id}"
    finished_key = f"finished:{well_id}"
    
    # 1) If we have a finished flag, report done
    if redis_client.exists(finished_key):
        return {"well_id": well_id, "status": "finished", "remaining": 0}
    
    # 2) If we still have a pending counter, report processing
    if redis_client.exists(pending_key):
        rem_val = redis_client.get(pending_key)
        if rem_val is None:
            rem = 0
        else:
            # Cast to bytes|str to help with type checking
            rem_val = cast(bytes | str, rem_val)
            decoded_val = rem_val.decode('utf-8') if isinstance(rem_val, bytes) else rem_val
            rem = int(decoded_val)
        return {"well_id": well_id, "status": "processing", "remaining": rem}
    
    # 3) Neither key exists → invalid well_id
    raise HTTPException(status_code=404,
                        detail=f"well_id '{well_id}' not found")

@router.post("/register_mask")
def register_mask_endpoint(request: Request, payload: RegisterMaskRequest) -> str | None:
    """
    Register a single mask and trigger tracking if it's an R2 mask.
    
    :param request: The FastAPI request object.
    :param payload: RegisterMaskRequest containing well_id, mask_path, total_fovs, and track_stitch_threshold
    
    :return: Task ID if tracking was triggered, None otherwise.
    """
    celery_app: Celery = request.app.state.celery_app
    
    # Register the mask
    fov_id, time_id, hkey = _register_single_mask(payload.well_id, payload.mask_path)
    
    # If it's an R2 mask ('2'), trigger tracking
    if time_id == '2':
        # Initialize the pending tracks counter if not already set
        redis_client.setnx(f"pending_tracks:{payload.well_id}", payload.total_fovs)
        redis_client.expire(f"pending_tracks:{payload.well_id}", 24 * 3600)
        
        # trigger tracking
        task = celery_app.send_task(
            'cp_server.tasks_server.tasks.counter.counter_task_manager.check_and_track',
            kwargs={
                'hkey': hkey,
                'track_stitch_threshold': payload.track_stitch_threshold})
        
        logger.debug(f"Registered R2 mask and triggered tracking task {task.id} for {fov_id}")
        return task.id
    else:
        logger.debug(f"Registered R1 mask for {fov_id}, no tracking triggered")
        return None
    
def _register_single_mask(well_id: str, mask_path: str) -> tuple[str, str, str]:
    """
    Helper function to register a single mask and extract FOV info.
    
    Args:
        well_id (str): The well ID
        mask_path (str): Path to the mask file
        
    Returns:
        tuple[str, str, str]: (fov_id, time_id, hkey)
    """
    path_obj = Path(mask_path)
    stem_parts = path_obj.stem.split('_')
    
    # For pattern <fov_id>_<category>_<time_id>, extract correctly
    fov_id = '_'.join(stem_parts[:-2])  # Everything except last 2 parts (category and time_id)
    time_id = stem_parts[-1]  # Last part is time_id
    
    hkey = f"masks:{well_id}:{fov_id}"
    redis_client.hset(hkey, time_id, mask_path)
    
    logger.debug(f"Registered R{time_id} mask for {fov_id}: {mask_path}")
    return fov_id, time_id, hkey

