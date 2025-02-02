from fastapi import APIRouter, Request

from cp_server import logger
from cp_server.celery_server.celery_task import mock_task
router = APIRouter()

@router.post("/segment")
def segment_task(request: Request, start_observer: bool = False):
    """Start a Celery task to process images with Cellpose."""
    
    # Get the source and destination directories
    src_dir = request.app.state.src_dir
    dst_dir = request.app.state.dst_dir
    
    if start_observer:
        logger.info(f"Starting observer for {src_dir}")
        raise NotImplementedError
    
    logger.info(f"Starting image processing task from {src_dir}")
    
    
    mock_task.delay(src_dir, dst_dir)
    return {"message": f"Processing started for {src_dir} and will be saved to {dst_dir}"}
