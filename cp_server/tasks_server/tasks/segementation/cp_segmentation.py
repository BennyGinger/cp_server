from __future__ import annotations
import threading
import warnings
from typing import Any, TypeVar
from concurrent.futures import ThreadPoolExecutor

from numpy.typing import NDArray
import numpy as np

from cp_server.tasks_server import get_logger
### Lazy import ### 
# from cellpose_kit.api import run_cellpose
# from cp_server.tasks_server.tasks.segementation.model_manager import model_manager


T = TypeVar("T", bound=np.generic)
DEFAULT_SEGMENT_THREADS = 4  # Default number of threads for batch segmentation

# Suppress FutureWarning messages from cellpose
warnings.filterwarnings("ignore", category=FutureWarning, module="cellpose")

logger = get_logger(__name__)


#########################################################################
########################## Main Function ################################
#########################################################################
def segment_image(img: NDArray[T] | list[NDArray[T]], cellpose_settings: dict[str, Any]) -> NDArray[T] | list[NDArray[T]]:
    """
    Generic segmentation interface for Cellpose using persistent model management.
    Uses model_manager to cache and reuse models for efficiency.
    Optionally runs batch segmentation in parallel using ThreadPoolExecutor.
    Args:
        img: Single image or list of images (np.ndarray or list of np.ndarray)
        cellpose_settings: Dict of cellpose-kit settings
        threads: Number of threads for batch processing (default 1 = no threading)
    Returns:
        Segmentation mask(s) (same type/shape as input)
    """
    from cellpose_kit.api import run_cellpose  # Lazy import
    from cp_server.tasks_server.tasks.segementation.model_manager import model_manager
    
    configured_settings = model_manager.get_configured_settings(cellpose_settings)
    if isinstance(img, list):
        logger.info(f"Running segment_image on batch with settings: {cellpose_settings}, threads={DEFAULT_SEGMENT_THREADS}")
        def _seg_single(im: NDArray[T]) -> NDArray[T]:
            masks, *_ = run_cellpose(im, configured_settings)
            assert isinstance(masks, np.ndarray), f"Expected NDArray but got {type(masks)}"
            return masks
        with ThreadPoolExecutor(max_workers=DEFAULT_SEGMENT_THREADS) as executor:
            results = list(executor.map(_seg_single, img))
        return results 
    else:
        logger.info(f"Running segment_image on single image with settings: {cellpose_settings}")
        masks, *_ = run_cellpose(img, configured_settings)
        return masks