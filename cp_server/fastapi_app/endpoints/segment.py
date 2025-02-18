from pathlib import Path

from fastapi import APIRouter, Request
from celery import Celery

from cp_server.fastapi_app import logger
from cp_server.fastapi_app.endpoints.utils import PayLoadSegement


router = APIRouter()


@router.post("/segment")
def segment_task(request: Request, payload: PayLoadSegement) -> dict:
    """Start a Celery task to process images with Cellpose."""
    
    # Get the source and destination directories
    celery_app: Celery = request.app.state.watcher_manager.celery_app
    directory = Path(payload.directory)
    
    logger.info(f"Starting image processing task from {directory}")
    logger.debug(f"{list(directory.rglob('*.tif'))=}")
    for img_file in directory.rglob("*.tif"):
        # Check that parent dir has the same name as the src_folder
        if img_file.parent.name != payload.src_folder:
            continue
        
        # Ignore non-key_label images
        if payload.key_label not in img_file.name:
            continue
        logger.debug(f"Processing image: {img_file}")
        # Execute celery's task
        celery_app.send_task("cp_server.tasks_server.celery_tasks.process_images", kwargs={
            "settings": payload.settings,
            "img_file": str(img_file),
            "dst_folder": payload.dst_folder,
            "key_label": payload.key_label,
            "do_denoise": payload.do_denoise,
        })
        
    return {"message": f"Processing images in {directory} with settings: {payload.settings}",}
