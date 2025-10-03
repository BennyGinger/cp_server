from collections import defaultdict
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
    - `img_path`: A string path or a list of string paths to image files.
    - `sigma`: Sigma value for background subtraction (default is 0.0).
    - `size`: Size parameter for background subtraction (default is 7).
    - `cellpose_settings`: Model and segmentation settings for Cellpose.
    - `dst_folder`: Destination folder where processed images will be saved.
    - `well_id`: Unique identifier for the processing well.
    - `total_fovs`: Total number of fields of view, used to set the number of pending tracks in Redis. Not included in the model dump.
    - `track_stitch_threshold`: Threshold for stitching masks during tracking. Optional, default is 0.75.
    - `round`: The round number for processing, build from the image path if not provided. Defaults to None. Not included in the model dump.
    This endpoint will send tasks to a Celery worker to process the images (single or batch).
    It returns a dictionary with the task ID and the count of images sent.

    :param request: The FastAPI request object.
    :param payload: The payload containing the image processing parameters.

    :return: A dictionary with task ID and count of images sent.
    """
    celery_app: Celery = request.app.state.celery_app

    # Initialize the counter for pending tracks
    if payload.round == 2:
        redis_client.setnx(f"pending_tracks:{payload.well_id}", payload.total_fovs)
        redis_client.expire(f"pending_tracks:{payload.well_id}", 24 * 3600)

    img_count = len(payload.img_path) if isinstance(payload.img_path, list) else 1
    logger.info(f"Sending {img_count} image(s) for processing with well_id {payload.well_id}")

    # Process the paths
    params = payload.model_dump()
    task = celery_app.send_task(
        "cp_server.tasks_server.tasks.celery_main_task.process_images",
        kwargs=params)

    # Determine number of images sent
    return {"well_id": payload.well_id, "task_id": task.id, "images_sent": img_count}

@router.post("/process_bg_sub")
def process_bg_sub_endpoint(request: Request, payload: BackgroundRequest) -> dict[str, Any]:
    """
    Endpoint to process background subtraction for images.
    This endpoint accepts a payload containing:
    - `img_path`: A string path or a list of string paths to image files.
    - `sigma`: Sigma value for background subtraction (default is 0.0).
    - `size`: Size parameter for background subtraction (default is 7).

    This endpoint will send tasks to a Celery worker to process the images (single or batch).
    It returns a dictionary with the task ID and the count of images sent.

    :param request: The FastAPI request object.
    :param payload: The payload containing the background subtraction parameters.

    :return: A dictionary with task ID and count of images sent.
    """
    celery_app: Celery = request.app.state.celery_app

    img_count = len(payload.img_path) if isinstance(payload.img_path, list) else 1
    logger.info(f"Sending {img_count} image(s) for background subtraction")

    # Process the paths
    params = payload.model_dump()
    task = celery_app.send_task(
        "cp_server.tasks_server.tasks.bg_sub.remove_bg",
        kwargs=params)

    return {"task_id": task.id, "images_sent": img_count}

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
def register_mask_endpoint(request: Request, payload: RegisterMaskRequest) -> list[str]:
    """
    Register multiple masks in batch and trigger tracking for R2 masks.
    
    :param request: The FastAPI request object.
    :param payload: RegisterMaskRequest containing well_id, mask_paths (list), total_fovs, and track_stitch_threshold

    :return: List of tracking task IDs.
    """
    celery_app: Celery = request.app.state.celery_app
    
    tracking_task_ids = []
    
    logger.info(f"Processing batch registration of {len(payload.mask_paths)} masks for well {payload.run_id}")
    
    # Early return for empty list
    if not payload.mask_paths:
        return []
    
    # Group masks by well_id
    masks_by_well_id = defaultdict(list)
    for mask_path in payload.mask_paths:
        path_obj = Path(mask_path)
        # Extract well from filename: e.g. A1P1_mask_2.tif → A1
        stem = path_obj.stem
        well = stem.split('P')[0]
        well_id = f"{payload.run_id}_{well}"
        masks_by_well_id[well_id].append(mask_path)
    
    for well_id, mask_paths in masks_by_well_id.items():
        # Check if there are any R2 masks to process
        r2_masks = [path for path in mask_paths if Path(path).stem.split('_')[-1] == '2']
        has_r2_masks = len(r2_masks) > 0
        
        # Only initialize pending_tracks if we have R2 masks to track
        if has_r2_masks:
            # Clear any existing finished flag (in case R1 was registered first)
            redis_client.delete(f"finished:{well_id}")
            # Set counter to total FOVs - this accounts for both registered R2 masks AND future R2 masks from imaging
            redis_client.setnx(f"pending_tracks:{well_id}", payload.total_fovs)
            redis_client.expire(f"pending_tracks:{well_id}", 24 * 3600)
        
        # Process all masks, but sort to ensure R1 masks are registered before R2 masks
        sorted_masks = sorted(mask_paths, key=lambda path: Path(path).stem.split('_')[-1])
        
        for mask_path in sorted_masks:
            try:
                fov_id, time_id, hkey = _register_single_mask(payload.run_id, mask_path)
                
                # Only trigger tracking for R2 masks
                if time_id == '2':
                    # Trigger tracking for R2 mask
                    task = celery_app.send_task(
                        'cp_server.tasks_server.tasks.counter.counter_task_manager.check_and_track',
                        kwargs={
                            'hkey': hkey,
                            'track_stitch_threshold': payload.track_stitch_threshold
                        }
                    )
                    tracking_task_ids.append(task.id)
                    logger.debug(f"Triggered tracking task {task.id} for {fov_id} (well {payload.run_id})")

            except Exception as e:
                logger.error(f"Failed to register mask {mask_path}: {e}")
                # Continue with other masks rather than failing entire batch
    
    logger.info(f"Batch registration completed: {len(payload.mask_paths)} masks processed, {len(tracking_task_ids)} tracking tasks")
    
    return tracking_task_ids
    
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

