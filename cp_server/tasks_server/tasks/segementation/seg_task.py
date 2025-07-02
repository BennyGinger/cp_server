from typing import Any
from celery import shared_task
import numpy as np

from cp_server.tasks_server import get_logger
from cp_server.tasks_server.tasks.saving.save_arrays import generate_mask_path, save_mask, extract_fov_id
from cp_server.tasks_server.tasks.segementation.cp_seg import run_seg
from cp_server.tasks_server.utils.redis_com import redis_client


logger = get_logger(__name__)

@shared_task(name="cp_server.tasks_server.tasks.segementation.seg_task.segment")
def segment(img: np.ndarray, 
            cellpose_settings: dict[str, Any],
            img_path: str, 
            dst_folder: str,
            well_id: str, 
            ) -> str:
    """
    Segment the image using Cellpose. Note that the image (ndarray) is encoded as a base64 string
    Args:
        img (np.ndarray): The image to be segmented.
        cellpose_settings (dict): Settings for the Cellpose model and segmentation.
        img_path (str): Path to the image file.
        dst_folder (str): Destination folder where the masks will be saved.
        well_id (str): Unique identifier for the processing run.
    """
    # Log the settings
    logger.info(f"Initializing segmentation for {img_path} with settings: {cellpose_settings}")
    logger.debug(f"Decoding img inside segment {img.shape=} and {img.dtype=}")
    
    # Run the segmentation
    mask = run_seg(cellpose_settings, img)
    logger.debug(f"Created cp masks of {mask.shape=}")
    
    # Encode the mask and save it in the background
    logger.info(f"Segmentation completed for {img_path}. Saving masks in {dst_folder}")
    mask_path = generate_mask_path(img_path, dst_folder)
    save_mask(mask, str(mask_path))
    
    # Extract fovID and timepoint from the image file name
    fov_id, time_id = extract_fov_id(img_path)
    logger.debug(f"Extracted fov_id: {fov_id} and time_id: {time_id} from {mask_path}")
    
    # Register the well_id and fov_id in Redis
    hkey = f"masks:{well_id}:{fov_id}"
    redis_client.hset(hkey, time_id, str(mask_path))
    logger.info(f"Stored mask for {fov_id} time {time_id}")
    return hkey