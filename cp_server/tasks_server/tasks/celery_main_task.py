from typing import Any
from celery import chain, shared_task
import tifffile as tiff

from cp_server.tasks_server import get_logger
from cp_server.tasks_server.tasks.bg_sub.bg_sub_task import remove_bg
from cp_server.tasks_server.tasks.counter.counter_task_manager import check_and_track
from cp_server.tasks_server.tasks.segementation.seg_task import segment

# Setup logging
logger = get_logger('tasks')


@shared_task(name="cp_server.tasks_server.tasks.celery_main_task.process_images")
def process_images(mod_settings: dict[str, Any],
                   cp_settings: dict[str, Any], 
                   img_file: str, 
                   dst_folder: str, 
                   round: int,
                   run_id: str,
                   do_denoise: bool=True,
                   stitch_threshold: float=0.75, 
                   sigma: float=0.0, 
                   size: int=7,
                   ) -> str:
    """
    Process images with background subtraction and segmentation. Note that the image (ndarray) is encoded as a base64 string.
    This function orchestrates the workflow of removing background, segmenting the image, and tracking cells if necessary.
    It initializes the tracking counter in Redis if this is the second round of processing and total_fovs is provided.
    It also saves the processed images and masks to the specified destination folder.
    The function is designed to be called by a Celery worker, and it uses the `chain` feature to create a workflow of tasks.
    During round 2, tracking will be triggered automatically once two masks for the same field of view (FOV) are available (see `segment` task).
    
    Args:
        mod_settings (dict): Model settings for Cellpose.
        cp_settings (dict): Segmentation settings for Cellpose.
        img_file (str): Path to the image file to be processed.
        dst_folder (str): Destination folder where the masks will be saved.
        round (int): The current round of processing (1 or 2).
        do_denoise (bool, optional): Whether to apply denoising. Defaults to True.
        stitch_threshold (float, optional): Threshold for stitching masks. Defaults to 0.25.
        sigma (float, optional): Sigma value for background subtraction. Defaults to 0.0.
        size (int, optional): Size parameter for background subtraction. Defaults to 7."""
    
    # Starting point of the log
    logger.info(f"Received image file: {img_file}")
    logger.info(f"Setting denoise to {do_denoise}, round {round}")
    
    # load the image
    img = tiff.imread(img_file)
    logger.debug(f"{img.shape=} and {img.dtype=}")

    # Create the workflow
    chain(remove_bg.s(
                img=img, 
                img_path=img_file, 
                sigma=sigma, 
                size=size),
          segment.s(
                mod_settings=mod_settings,
                cp_settings=cp_settings,
                img_file=img_file,
                dst_folder=dst_folder, 
                run_id=run_id,
                do_denoise=do_denoise),
            check_and_track.s(stitch_threshold=stitch_threshold),
          ).apply_async()
    logger.info(f"Workflow created for {img_file}")
    return f"Image {img_file} was sent to be segmented"
