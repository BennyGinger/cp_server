from __future__ import annotations
import warnings
from typing import Any, Union, List, TypeVar


from numpy.typing import NDArray
import numpy as np
from cellpose_kit.api import setup_cellpose, run_cellpose

from cp_server.tasks_server import get_logger

T = TypeVar("T", bound=np.generic)

# Suppress FutureWarning messages from cellpose
warnings.filterwarnings("ignore", category=FutureWarning, module="cellpose")                

# Set up logging
logger = get_logger(__name__)

def run_seg(cellpose_settings: dict[str, Any], img: Union[NDArray[T], List[NDArray[T]]]) -> Union[NDArray[T], List[NDArray[T]]]:
    """
    Run segmentation on image(s) using Cellpose via cellpose_kit API.
    
    This function wraps the cellpose_kit API to provide a simplified interface for image
    segmentation. It preserves the input/output type relationship using TypeVar to ensure
    type safety.
    
    Input/Output Type Preservation:
    - Single NDArray[T] input → Single NDArray[T] output (same dtype)
    - List[NDArray[T]] input → List[NDArray[T]] output (same dtype)
    - Supports 2D, 3D, and 4D arrays
    
    Args:
        cellpose_settings (dict[str, Any]): Configuration dictionary for Cellpose model
            and segmentation parameters. Should include model_type, diameter, channels,
            flow_threshold, cellprob_threshold, etc. The 'do_denoise' parameter defaults
            to True if not specified.
        img (Union[NDArray[T], List[NDArray[T]]]): The image(s) to segment. Can be a
            single numpy array or a list of arrays for batch processing.
    
    Returns:
        Union[NDArray[T], List[NDArray[T]]]: Segmented masks with the same type and
        shape as the input. Pixel values represent object labels (0 = background,
        1+ = object IDs).
    
    Note:
        This function only returns the masks from run_cellpose. The flows and styles
        are discarded. Use cellpose_kit.api.run_cellpose directly if you need those.
    """
    
    # Extract do_denoise setting (defaults to True for backward compatibility)
    do_denoise = cellpose_settings.get("do_denoise", True)
    
    # Setup cellpose model and eval parameters
    configured_settings = setup_cellpose(
        cellpose_settings=cellpose_settings,
        threading=False,  # No threading needed for single image
        use_nuclear_channel=False,  # Can be made configurable later
        do_denoise=do_denoise
    )
    
    # Run segmentation, and only return the masks (same shape as the input image)
    return run_cellpose(img, configured_settings)[0]

if __name__ == "__main__":
    # Manual test
    
    from pathlib import Path
    from tifffile import imread, imwrite
    
    # Load image
    img_path = Path(r"D:\Ben\20250620_test\A1\A1_images\A1_P1_measure_1.tif")
    img = imread(img_path)
    
    # Load settings using the new format (compatible with cellpose_kit)
    cellpose_settings = {
        "model_type": "cyto3",
        "restore_type": "denoise_cyto3",
        "gpu": True,
        "channels": None,
        "diameter": 60,
        "flow_threshold": 0.4,
        "cellprob_threshold": 0.0,
        "z_axis": None,
        "do_3D": False,
        "stitch_threshold": 0,
        "do_denoise": True,
    }
    
    # Run segmentation
    masks = run_seg(cellpose_settings, img)
    
    # Save masks (handle both single array and list cases)
    if isinstance(masks, list):
        for i, mask in enumerate(masks):
            save_path = Path(r"D:\Ben\20250620_test\A1").joinpath(f"{img_path.name}_masks_{i}.tif")
            imwrite(save_path, mask.astype("uint16"), compression="zlib")
    else:
        save_path = Path(r"D:\Ben\20250620_test\A1").joinpath(f"{img_path.name}_masks.tif")
        imwrite(save_path, masks.astype("uint16"), compression="zlib")