from typing import Any

from celery import chain, shared_task

from cp_server.tasks_server import get_logger
from cp_server.tasks_server.celery_app import celery_app

# Setup logging
logger = get_logger('tasks')


@shared_task(name="cp_server.tasks_server.tasks.celery_main_task.process_images")
def process_images(img_path: str | list[str],
                   cellpose_settings: dict[str, Any],
                   dst_folder: str, 
                   well_id: str,
                   track_stitch_threshold: float=0.75, 
                   sigma: float=0.0, 
                   size: int=7,
                   ) -> str:
    """
    Process one or more images by removing the background, segmenting, and tracking using Cellpose and IoU tracking.
    Accepts a single image path or a list of image paths. Handles batch operation for all downstream tasks.
    """
    # Starting point of the log
    logger.info(f"Received image file(s): {img_path}")

    # Helper to create the workflow chain for a single or batch
    def create_chain(img_path_batch):
        return chain(
            celery_app.signature(
                'cp_server.tasks_server.tasks.bg_sub.remove_bg',
                kwargs=dict(
                    img_path=img_path_batch, 
                    sigma=sigma, 
                    size=size
                )
            ),
            celery_app.signature(
                'cp_server.tasks_server.tasks.segementation.seg_task.segment',
                kwargs=dict(
                    cellpose_settings=cellpose_settings, 
                    dst_folder=dst_folder, 
                    well_id=well_id
                )
            ),
            celery_app.signature(
                'cp_server.tasks_server.tasks.counter.counter_task_manager.check_and_track',
                kwargs=dict(
                    track_stitch_threshold=track_stitch_threshold
                )
            ),
        )

    # Accept both str and list[str]
    if isinstance(img_path, list):
        logger.info(f"Batch workflow: {len(img_path)} images.")
        # For batch, pass the list through the chain (all downstream tasks support batch)
        create_chain(img_path).apply_async()
        logger.info(f"Batch workflow created for {len(img_path)} images.")
        return f"Batch of {len(img_path)} images sent to be segmented"
    else:
        # Single image
        create_chain(img_path).apply_async()
        logger.info(f"Workflow created for {img_path}")
        return f"Image {img_path} was sent to be segmented"

    