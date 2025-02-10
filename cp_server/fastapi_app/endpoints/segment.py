from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from cp_server.fastapi_app import logger
from cp_server.task_server.celery_task import process_images


router = APIRouter()

class SegmentRequest(BaseModel):
    src_folder: str
    dst_folder: str
    key_label: str
    settings: dict[str, dict[str, Any]]
    do_denoise: bool = True

@router.post("/segment")
def segment_task(request: Request, payload: SegmentRequest, start_observer: bool=False):
    """Start a Celery task to process images with Cellpose."""
    
    # Get the source and destination directories
    mnt_dir = str(request.app.state.src_dir)
    
    if start_observer:
        logger.info(f"Starting observer for {mnt_dir}")
        raise NotImplementedError
    
    logger.info(f"Starting image processing task from {mnt_dir}")
    
    for img_file in mnt_dir.rglob("*.tif"):
        # Check that parent dir has the same name as the src_folder
        if img_file.parent.name != payload.src_folder:
            continue
        
        # Ignore non-key_label images
        if payload.key_label not in img_file.name:
            continue
        
        # Execute celery's task
        process_images.delay(payload.settings, img_file, payload.dst_folder, payload.key_label, payload.do_denoise)
        
    return {"message": f"Processing images in {mnt_dir} with settings: {payload.settings}",}
