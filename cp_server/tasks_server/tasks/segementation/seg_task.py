from typing import Any, TypeVar, Union, List
from celery import shared_task
import numpy as np
from tifffile import imread

from cp_server.tasks_server import get_logger
from cp_server.tasks_server.tasks.saving.save_arrays import generate_mask_path, save_mask, extract_fov_id
from cp_server.tasks_server.utils.redis_com import redis_client

# Import the segmentation backend interface (can be swapped for other algorithms)
from cp_server.tasks_server.tasks.segementation.cp_segmentation import segment_image

T = TypeVar("T", bound=np.generic)

logger = get_logger(__name__)

@shared_task(name="cp_server.tasks_server.tasks.segementation.seg_task.segment")
def segment(
    img_path: Union[str, List[str]],
    cellpose_settings: dict[str, Any],
    dst_folder: str,
    well_id: str,
) -> Union[str, List[str]]:
    """
    Segment one or more images using Cellpose with persistent model loading via cellpose-kit.
    Args:
        img_path (str | list[str]): Path(s) to the image file(s).
        cellpose_settings (dict): Settings for the Cellpose model and segmentation.
        dst_folder (str): Destination folder where the masks will be saved.
        well_id (str): Unique identifier for the processing run.
    Returns:
        str or list[str]: Redis key(s) for the stored mask(s).
    """
    if isinstance(img_path, list):
        logger.info(f"Batch segmenting {len(img_path)} images with settings: {cellpose_settings}")
        imgs = []
        for p in img_path:
            try:
                img = imread(p)
                logger.debug(f"Loaded image from {p} with shape {img.shape} and dtype {img.dtype}")
                imgs.append(img)
            except Exception as e:
                logger.error(f"Failed to read image from {p}: {e}")
                raise
        try:
            masks = segment_image(imgs, cellpose_settings)
        except Exception as e:
            logger.error(f"Batch segmentation failed: {e}")
            raise
        assert isinstance(masks, list) and len(masks) == len(img_path), "Batch output mismatch"
        hkeys = []
        for mask, p in zip(masks, img_path):
            mask_path = generate_mask_path(p, dst_folder)
            save_mask(mask, str(mask_path))
            hkey = _register_mask_in_redis(mask_path, p, well_id)
            hkeys.append(hkey)
        return hkeys
    else:
        logger.info(f"Initializing segmentation for {img_path} with settings: {cellpose_settings}")
        try:
            img = imread(img_path)
            logger.debug(f"Loaded image from {img_path} with shape {img.shape} and dtype {img.dtype}")
        except Exception as e:
            logger.error(f"Failed to read image from {img_path}: {e}")
            raise
        try:
            mask = segment_image(img, cellpose_settings)
        except Exception as e:
            logger.error(f"Segmentation failed for {img_path}: {e}")
            raise
        assert not isinstance(mask, list), f"Expected single mask but got list of {len(mask)} masks"
        logger.debug(f"Created masks of {mask.shape=}")
        mask_path = generate_mask_path(img_path, dst_folder)
        save_mask(mask, str(mask_path))
    hkey = _register_mask_in_redis(mask_path, img_path, well_id)
    return hkey

def _register_mask_in_redis(mask_path: str, img_path: str, well_id: str) -> str:
    fov_id, time_id = extract_fov_id(img_path)
    hkey = f"masks:{well_id}:{fov_id}"
    redis_client.hset(hkey, time_id, str(mask_path))
    logger.info(f"Stored mask for {fov_id} time {time_id} at {mask_path}")
    return hkey
