from pathlib import Path

from fastapi import APIRouter, Request, HTTPException
from celery import Celery

from cp_server.fastapi_app.endpoints.utils import ProcessRequest
from cp_server.logging import get_logger


# Setup logging
logger = get_logger('process_task')

# Create a router for the segment task
router = APIRouter()


@router.post("/process")
def process_images_endpoint(request: Request, payload: ProcessRequest) -> dict:
    """
    Endpoint to process images using the provided payload.
    This endpoint accepts a payload containing:
    - `img_file`: A string path to an image file, a directory containing images, or a list of image paths.
    - `mod_settings`: Settings for the model.
    - `cp_settings`: Settings for the Cellpose processing.
    - `dst_folder`: Destination folder where processed images will be saved.
    - `round`: The round number for processing.
    - `total_fovs`: Optional total number of fields of view.
    - `do_denoise`: Whether to apply denoising (default is True).
    - `stitch_threshold`: Threshold for stitching masks (default is 0.75).
    - `sigma`: Sigma value for background subtraction (default is 0.0).
    - `size`: Size parameter for background subtraction (default is 7).
    This endpoint will send tasks to a Celery worker to process the images.
    It returns a dictionary with the task IDs and the count of tasks sent.
    
    :param request: The FastAPI request object.
    :param payload: The payload containing the image processing parameters.
    
    :return: A dictionary with task IDs and count of tasks sent.
    
    :raises HTTPException: If the destination folder is not provided or does not exist.
    :raises ValueError: If the provided image paths are invalid or do not exist. 
    """
    # Get the source and destination directories
    celery_app: Celery = request.app.state.celery_app
    
    if not payload.dst_folder:
        raise HTTPException(status_code=400, detail="Provide a destination folder in dst_folder")
    
    if not Path(payload.dst_folder).exists():
        Path(payload.dst_folder).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Enqueuing {len(payload.image_paths)} images for processing (round={payload.round})")
    
    if payload.round == 2:
        total_fovs = payload.total_fovs or len(payload.image_paths)
    
    # Process the paths
    task_ids = []
    for path in payload.image_paths:
        params = payload.model_dump()
        params["img_file"] = path
        params['total_fovs'] = total_fovs if payload.round == 2 else None
        task = celery_app.send_task(
            "cp_server.tasks_server.celery_tasks.process_images",
            kwargs=params)
        task_ids.append(task.id)

    return {"task_ids": task_ids, "count": len(task_ids)}