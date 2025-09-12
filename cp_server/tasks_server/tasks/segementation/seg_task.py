from typing import Any
from celery import shared_task
import numpy as np

from cp_server.tasks_server import get_logger
from cp_server.tasks_server.tasks.saving.save_arrays import generate_mask_path, save_mask, extract_fov_id
from cp_server.tasks_server.utils.redis_com import redis_client
from cp_server.tasks_server.tasks.segementation.model_manager import model_manager


logger = get_logger(__name__)

@shared_task(name="cp_server.tasks_server.tasks.segementation.seg_task.segment")
def segment(img: np.ndarray, 
            cellpose_settings: dict[str, Any],
            img_path: str, 
            dst_folder: str,
            well_id: str, 
            ) -> str:
    """
    Segment the image using Cellpose with persistent model loading via cellpose-kit.
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
    
    # Get cached configured settings from cellpose-kit
    configured_settings = model_manager.get_configured_settings(cellpose_settings)
    
    # Run segmentation with cellpose-kit
    try:
        mask = _run_segmentation_with_cellpose_kit(configured_settings, img)
    except Exception as e:
        logger.error(f"Segmentation failed for {img_path}: {e}")
        raise
    
    # Since we pass a single array, we expect a single array back
    assert not isinstance(mask, list), f"Expected single mask but got list of {len(mask)} masks"
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


def _run_segmentation_with_cellpose_kit(configured_settings: Any, img: np.ndarray) -> np.ndarray:
    """Run segmentation using cellpose-kit with pre-configured settings"""
    try:
        from cellpose_kit.api import run_cellpose
        
        # Run segmentation - cellpose-kit handles threading, model management, etc.
        masks, flows, styles = run_cellpose(img, configured_settings)
        return masks
    except Exception as e:
        logger.error(f"Cellpose-kit evaluation failed: {e}")
        raise