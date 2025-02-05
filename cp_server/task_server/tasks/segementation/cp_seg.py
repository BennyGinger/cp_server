import warnings

import numpy as np
from cellpose.denoise import CellposeDenoiseModel
from cellpose.models import CellposeModel

from cp_server.task_server import celery_logger

# Suppress FutureWarning messages from cellpose
warnings.filterwarnings("ignore", category=FutureWarning, module="cellpose")                


def run_seg(settings: dict[str, dict], img: np.ndarray, do_denoise: bool=True)-> np.ndarray:
    
    # Unpack settings
    model_settings, cp_settings = unpack_settings(settings, do_denoise)
    
    # Initialize Cellpose model
    model = initialize_cellpose_model(do_denoise, model_settings)
    celery_logger.debug(f"Loading {type(model)} model with {model_settings}")
    
    # Run segmentation
    celery_logger.debug(f"Running eval with {cp_settings}")
    masks = segment_image(img, cp_settings, model)
    celery_logger.debug(f"{masks.shape=}")
    
    return masks


##################### Helper functions #####################
def unpack_settings(settings: dict, do_denoise: bool)-> tuple[dict,dict]:
    """Unpack the settings for the model and segmentation"""
    
    # Unpack settings
    mod_set = settings.get("model", {})
    cp_set = settings.get("segmentation", {})
    
    # No denoise, remove restore_type
    if not do_denoise:
        if "restore_type" in mod_set:
            del mod_set["restore_type"]
        
        return mod_set, cp_set
    
    # Catch the channels bug from cellpose: default val is None, but denoise model requires a list
    if "channels" not in cp_set:
        cp_set["channels"] = [0, 0]
        return mod_set, cp_set
    
    if cp_set["channels"] is None:
        cp_set["channels"] = [0, 0]
        return mod_set, cp_set
    
    return mod_set, cp_set

def initialize_cellpose_model(do_denoise: bool, model_settings: dict)-> CellposeModel | CellposeDenoiseModel:
    """Initialize the Cellpose model"""
    
    if do_denoise:
        return CellposeDenoiseModel(**model_settings)
    return CellposeModel(**model_settings)

def segment_image(img: np.ndarray, cp_settings: dict, model: CellposeModel | CellposeDenoiseModel)-> np.ndarray:
    """Run the segmentation on the image"""
    
    return model.eval(img, **cp_settings)[0]


if __name__ == "__main__":
    # Manual test
    
    from pathlib import Path
    from tifffile import imread, imwrite
    
    # Load image
    img_path = Path("/media/ben/Analysis/Python/cp_server/Image_tests/src_test/z25_t1.tif")
    img = imread(img_path)
    
    # Load settings
    settings = {"model":{
                    "model_type": "cyto2",
                    "restore_type": "denoise_cyto2",
                    "gpu": True,
                        },
                "segmentation": {
                                "channels": None,
                                "diameter": 60,
                                "flow_threshold": 0.4,
                                "cellprob_threshold": 0.0,
                                "z_axis": 0,
                                "do_3D": False,
                                "stitch_threshold": 0.75,}
                }
    
    # Run segmentation
    masks = run_seg(settings, img, False)
    
    # Save masks
    save_path = Path("/media/ben/Analysis/Python/cp_server/Image_tests/dst_test").joinpath(f"{img_path.name}_masks.tif")
    imwrite(save_path, masks.astype("uint16"))