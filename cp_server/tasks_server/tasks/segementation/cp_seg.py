import warnings
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from cellpose.denoise import CellposeDenoiseModel
    from cellpose.models import CellposeModel

# Suppress FutureWarning messages from cellpose
warnings.filterwarnings("ignore", category=FutureWarning, module="cellpose")                


def run_seg(model_settings: dict[str, any],
            cp_settings: dict[str, any],
            img: np.ndarray, 
            do_denoise: bool=True,
            ) -> np.ndarray:
    
    # Unpack settings
    model_settings = _update_model_parameters(model_settings, do_denoise)
    cp_settings = _update_cp_settings(cp_settings, do_denoise)
    
    # Initialize Cellpose model
    model = _initialize_cellpose_model(do_denoise, model_settings)
    
    # Run segmentation
    masks = segment_image(img, cp_settings, model)
    
    return masks


##################### Helper functions #####################
def _update_model_parameters(mod_set: dict[str, any],
                            do_denoise: bool=True,
                            ) -> dict[str, any]:
    """
    Validate the model settings and add restore_type if needed.
    """
    if not do_denoise:
        if "restore_type" in mod_set:
            del mod_set["restore_type"]
        return mod_set
    
    if "restore_type" not in mod_set:
        mod_set["restore_type"] = "denoise_cyto3" if mod_set["model_type"] == "cyto3" else "denoise_cyto2"
        return mod_set
    
def _update_cp_settings(cp_set: dict[str, any],
                          do_denoise: bool=True,
                          ) -> dict[str, any]:
     """
     Validate the Cellpose settings and add channels if needed.
     """
     if not do_denoise:
          return cp_set
     
     # Catch the channels bug from cellpose: default val is None, but denoise model requires a list
     if "channels" not in cp_set or cp_set["channels"] is None:
          cp_set["channels"] = [0, 0]
     
     return cp_set

def _initialize_cellpose_model(do_denoise: bool, model_settings: dict)-> CellposeModel | CellposeDenoiseModel:
    """
    Initialize the Cellpose model, with lazy import to avoid unnecessary dependencies.
    """
    
    if do_denoise:
        from cellpose.denoise import CellposeDenoiseModel
        return CellposeDenoiseModel(**model_settings)
    from cellpose.models import CellposeModel
    return CellposeModel(**model_settings)

def segment_image(img: np.ndarray, cp_settings: dict, model: CellposeModel | CellposeDenoiseModel)-> np.ndarray:
    """
    Run the segmentation on the image
    """
    
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