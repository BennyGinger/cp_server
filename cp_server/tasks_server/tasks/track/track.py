import numpy as np
from skimage.segmentation import relabel_sequential

from cp_server.tasks_server.tasks.track.track_utils import stitch_frames, trim_incomplete_tracks


def track_masks(masks: np.ndarray, stitch_threshold: float=0.25) -> np.ndarray:
    """Track cells over time by stitching 2D masks into a time sequence using a stitch_threshold on IOU. Incomplete tracks are also automatically trimmed.

    Args:
        masks (ndarray): stack of masks, where masks[t] is a 2D array of masks at time t.
        stitch_threshold (float, optional): Threshold value for stitching. Defaults to 0.25.

    Returns:
        ndarray: stitched masks.
    """
    
    stitched_masks = stitch_frames(masks, stitch_threshold)
    trimmed_mask = trim_incomplete_tracks(stitched_masks)
    
    
    return trimmed_mask