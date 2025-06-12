from typing import Any
from celery import chain, shared_task

from cp_server.tasks_server import get_logger
from cp_server.tasks_server.tasks.bg_sub.bg_sub_task import remove_bg
from cp_server.tasks_server.tasks.counter.counter_task_manager import check_and_track
from cp_server.tasks_server.tasks.segementation.seg_task import segment

# Setup logging
logger = get_logger('tasks')


@shared_task(name="cp_server.tasks_server.tasks.celery_main_task.process_images")
def process_images(mod_settings: dict[str, Any],
                   cp_settings: dict[str, Any], 
                   img_path: str, 
                   dst_folder: str, 
                   round: int,
                   run_id: str,
                   do_denoise: bool=True,
                   track_stitch_threshold: float=0.75, 
                   sigma: float=0.0, 
                   size: int=7,
                   ) -> str:
    """
    Process an image by removing the background, segmenting and tracking it using Cellpose and IoU tracking.
    This task is designed to be run in a Celery worker, where background subtraction and segmentation are always performed.
    Tracking is only triggered if round is 2 or above. The image is loaded from the provided file path, and the results are saved
    in the specified destination folder. The function logs the process and returns a message indicating the status of the operation.
    
    Args:
        mod_settings (dict): Model settings for Cellpose.
        cp_settings (dict): Segmentation settings for Cellpose.
        img_path (str): Path to the image file to be processed.
        dst_folder (str): Destination folder where the masks will be saved.
        round (int): The current round of processing (1 or 2).
        run_id (str): Unique identifier for the processing run.
        do_denoise (bool, optional): Whether to apply denoising. Defaults to True.
        track_stitch_threshold (float, optional): Threshold for stitching masks. Defaults to 0.25.
        sigma (float, optional): Sigma value for background subtraction. Defaults to 0.0.
        size (int, optional): Size parameter for background subtraction. Defaults to 7."""
    
    # Starting point of the log
    logger.info(f"Received image file: {img_path}")
    logger.info(f"Setting denoise to {do_denoise}, round {round}")
    
    #### Create the workflows ####
    chain(remove_bg.s(
                img_path=img_path, 
                sigma=sigma, 
                size=size),
        segment.s(
                mod_settings=mod_settings,
                cp_settings=cp_settings,
                img_file=img_path,
                dst_folder=dst_folder, 
                run_id=run_id,
                do_denoise=do_denoise),
            check_and_track.s(track_stitch_threshold=track_stitch_threshold,),
        ).apply_async()
    logger.info(f"Workflow created for {img_path}")
    return f"Image {img_path} was sent to be segmented"

    