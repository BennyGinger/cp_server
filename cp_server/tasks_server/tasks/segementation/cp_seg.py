from __future__ import annotations
import warnings
from typing import TYPE_CHECKING, Any

from tasks_server import get_logger
import numpy as np

if TYPE_CHECKING:
    from cellpose.denoise import CellposeDenoiseModel
    from cellpose.models import CellposeModel

# Suppress FutureWarning messages from cellpose
warnings.filterwarnings("ignore", category=FutureWarning, module="cellpose")                

# Set up logging
logger = get_logger(__name__)

MOD_SETS = {"model_type": "cyto2",
                "restore_type": "denoise_cyto2",
                "gpu": True,}

EVAL_SETS = {"channels": None,
               "diameter": 60,
               "flow_threshold": 0.4,
               "cellprob_threshold": 0.0,
               "z_axis": None,
               "do_3D": False,
               "stitch_threshold_3D": 0,}


# TODO: Update to cellpose 4.0
def run_seg(cellpose_settings: dict[str, Any], img: np.ndarray) -> np.ndarray:
    """
    Run segmentation on the image using Cellpose.
    Args:
        model_settings (dict): Settings for the Cellpose model.
        cp_settings (dict): Settings for the Cellpose segmentation.
        img (np.ndarray): The image to segment.
        do_denoise (bool): Whether to use denoising model or not. Default is True.
    Returns:
        np.ndarray: The segmented masks."""
    
    # Unpack settings
    do_denoise = cellpose_settings.pop("do_denoise", True)
    mod_sets, eval_sets = _unpack_cellpose_settings(cellpose_settings, do_denoise)
    
    # Initialize Cellpose model
    model = _initialize_cellpose_model(do_denoise, mod_sets)
    
    # Run segmentation
    return _segment_image(img, eval_sets, model)


##################### Helper functions #####################
def _unpack_cellpose_settings(cellpose_settings: dict[str, Any], do_denoise: bool) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Unpack the Cellpose settings into model and segmentation settings.
    Args:
        cellpose_settings (dict): The settings dictionary containing both model and segmentation parameters.
        do_denoise (bool): Whether to use the denoising model or not.
    Returns:
        tuple: A tuple containing two dictionaries:
            - mod_sets: Model settings for Cellpose.
            - eval_sets: Run settings for Cellpose.
    """
    mod_sets = MOD_SETS.copy()
    eval_sets = EVAL_SETS.copy()
    
    for sets in (eval_sets, mod_sets):
        # pick out only the overrides that belong in this dict
        overrides = {k: v for k, v in cellpose_settings.items() if k in sets}
        sets.update(overrides)
    
    return _update_model_parameters(mod_sets, do_denoise), _update_eval_settings(eval_sets, do_denoise)

def _update_model_parameters(mod_set: dict[str, Any], do_denoise: bool=True) -> dict[str, Any]:
    """
    Validate the model settings and add restore_type if needed.
    Args:
        mod_set (dict): The settings dictionary containing Cellpose model parameters.
        do_denoise (bool): Whether to use the denoising model or not.
    Returns:
        dict: The updated model settings for Cellpose.
    """
    if not do_denoise:
        if "restore_type" in mod_set:
            del mod_set["restore_type"]
        return mod_set
    
    if "restore_type" not in mod_set:
        mod_set["restore_type"] = "denoise_cyto3" if mod_set["model_type"] == "cyto3" else "denoise_cyto2"
        return mod_set
    return mod_set
    
def _update_eval_settings(cp_set: dict[str, Any], do_denoise: bool=True) -> dict[str, Any]:
     """
     Validate the eval settings and add channels if needed.
     Args:
         cp_set (dict): The settings dictionary containing Cellpose evaluation parameters.
         do_denoise (bool): Whether to use the denoising model or not.
     Returns:
         dict: The updated evaluation settings for Cellpose.
     """
     # Convert 3d_stitch_threshold to stitch_threshold if needed
     if "stitch_threshold_3D" in cp_set:
          cp_set["stitch_threshold"] = cp_set.pop("stitch_threshold_3D")
     
     if not do_denoise:
          return cp_set
     
     # Catch the channels bug from cellpose: default val is None, but denoise model requires a list
     if "channels" not in cp_set or cp_set["channels"] is None:
          cp_set["channels"] = [0, 0]
     
     return cp_set

def _initialize_cellpose_model(do_denoise: bool, model_settings: dict[str, Any])-> CellposeModel | CellposeDenoiseModel:
    """
    Initialize the Cellpose model, with lazy import to avoid unnecessary dependencies.
    """
    
    if do_denoise:
        from cellpose.denoise import CellposeDenoiseModel
        model = CellposeDenoiseModel(**model_settings)
        logger.debug(f"Cellpose is using GPU: {model.cp.gpu}")
        return model
    
    from cellpose.models import CellposeModel
    model = CellposeModel(**model_settings)
    logger.debug(f"Cellpose is using GPU: {model.gpu}")
    return model

def _segment_image(img: np.ndarray, eval_settings: dict, model: CellposeModel | CellposeDenoiseModel)-> np.ndarray:
    """
    Run the segmentation on the image
    """
    
    return model.eval(img, **eval_settings)[0]


if __name__ == "__main__":
    # Manual test
    
    from pathlib import Path
    from tifffile import imread, imwrite
    
    # Load image
    img_path = Path(r"D:\Ben\20250620_test\A1\A1_images\A1_P1_measure_1.tif")
    img = imread(img_path)
    
    # Load settings
    mod_sets = {"model_type": "cyto3",
                "restore_type": "denoise_cyto3",
                "gpu": True,}
    
    cp_sets = {"channels": None,
               "diameter": 60,
               "flow_threshold": 0.4,
               "cellprob_threshold": 0.0,
               "z_axis": None,
               "do_3D": False,
               "stitch_threshold": 0,}
    cel_sets = {**mod_sets, **cp_sets}
    # Run segmentation
    masks = run_seg(cel_sets, img)
    
    # Save masks
    save_path = Path(r"D:\Ben\20250620_test\A1").joinpath(f"{img_path.name}_masks.tif")
    imwrite(save_path, masks.astype("uint16"), compression="zlib")