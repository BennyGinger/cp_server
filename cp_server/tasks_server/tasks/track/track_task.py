from celery import shared_task
import numpy as np
import tifffile as tiff

from cp_server.tasks_server import get_logger
from cp_server.tasks_server.tasks.saving.save_arrays import save_mask
from cp_server.tasks_server.tasks.track.track import track_masks


logger = get_logger(__name__)

@shared_task(name="cp_server.tasks_server.tasks.track.track_cells")
def track_cells(mask_paths: list[str], 
                track_stitch_threshold: float,
                ) -> None:
    """
    Task to track cells in a time series of images. Masks are stitched together based on a threshold for IOU (Intersection Over Union).
    Masks are then relabeled sequentially to ensure unique labels across the time series.
    """
    
    # Log
    logger.info(f"Tracking cells in {len(mask_paths)} images with track_stitch_threshold {track_stitch_threshold}")
    
    # Load the stack of masks
    masks = [tiff.imread(path) for path in mask_paths]
    masks = np.array(masks).astype(np.uint16)
    logger.debug(f"Loaded masks of shape {masks.shape=}")
    
    # Track the cells and trim the masks
    stitched_masks = track_masks(masks, track_stitch_threshold)
    logger.debug(f"Stitched masks of shape {stitched_masks.shape=}")
    
    # Overwrite the original masks with the stitched ones
    for mask, path in zip(stitched_masks, mask_paths):
        save_mask(mask, path)