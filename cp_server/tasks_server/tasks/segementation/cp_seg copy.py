# Foundation for the Cellpose 4.0, I will need to update this with maybe a pydantic model to make sure the inputs are correct.

from __future__ import annotations
import warnings
from typing import TYPE_CHECKING, TypeVar

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from cellpose.models import CellposeModel

# Suppress FutureWarning messages from cellpose
warnings.filterwarnings("ignore", category=FutureWarning, module="cellpose")                

T = TypeVar("T", bound=np.generic)


MOD_SETS = {
    "gpu": True, # Whether or not to save model to GPU, will check if GPU available.
    "pretrained_model": "cpsam", # path to pretrained model, or str of built-in model name i.e. ['cpsam']
    "model_type": None, # Decrepated in cellpose 4.0
    "diam_mean": None, # Decrepated in cellpose 4.0
    "device": None, # Device used for model running / training (torch.device("cuda") or torch.device("cpu")), overrides gpu input, recommended if you want to use a specific GPU (e.g. torch.device("cuda:1")).
    "nchan": None, # Decrepated in cellpose 4.0
    "use_bfloat16": True, # Use 16bit float precision instead of 32bit for model weights. Default to 16bit (True).
    }

EVAL_SETS = {
    "batch_size": 8, # number of 256x256 patches to run simultaneously on the GPU (smaller or bigger depending on GPU memory). Defaults to 64.
    "resample": True, # run dynamics at original image size (will be slower but create more accurate boundaries).
    "channels": None, # Decrepated in cellpose 4.0
    "channel_axis": None, # # Decrepated in cellpose 4.0
    "z_axis": None, # z axis in element of list x, or of np.ndarray x. if None, z dimension is automatically determined. Defaults to None.
    "normalize": True, # if True, normalize data so 0.0=1st percentile and 1.0=99th percentile of image intensities in each channel; can also pass dictionary of parameters (all keys are optional, default values shown in normalize_default)
    "invert": False, # invert image pixel intensity before running network. Defaults to False.
    "rescale": None, # resize factor for each image, if None, set to 1.0; (only used if diameter is None). Defaults to None.
    "diameter": None, # diameters are used to rescale the image to 30 pix cell diameter.
    "flow_threshold": 0.4, # flow error threshold (all cells with errors below threshold are kept) (not used for 3D). Defaults to 0.4.
    "cellprob_threshold": 0.0, # all pixels with value above threshold kept for masks, decrease to find more and larger masks. Defaults to 0.0.
    "do_3D": False, # set to True to run 3D segmentation on 3D/4D image input. Defaults to False.
    "anisotropy": None, # for 3D segmentation, optional rescaling factor (e.g. set to 2.0 if Z is sampled half as dense as X or Y). Defaults to None.
    "flow3D_smooth": 0, # if do_3D and flow3D_smooth>0, smooth flows with gaussian filter of this stddev. Defaults to 0.
    "stitch_threshold_3D": 0, # if stitch_threshold>0.0 and not do_3D, masks are stitched in 3D to return volume segmentation. Defaults to 0.0.
    "min_size": 15, # all ROIs below this size, in pixels, will be discarded. Defaults to 15.
    "max_size_fraction": 0.4, # max_size_fraction (float, optional): Masks larger than max_size_fraction of total image size are removed. Default is 0.4.
    "niter": None, # Number of iterations for dynamics computation. if None, it is set proportional to the diameter. Defaults to None.
    "augment": False, # tiles image with overlapping tiles and flips overlapped regions to augment. Defaults to False.
    "tile_overlap": 0.1, # fraction of overlap of tiles when computing flows. Defaults to 0.1.
    "bsize": 256, # block size for tiles, recommended to keep at 224, like in training. Defaults to 224.
    "compute_masks": True, # Whether or not to compute dynamics and return masks. Returns empty array if False. Defaults to True.
    "progress": None, # pyqt progress bar. Defaults to None.
    }

normalize_default = {
    "lowhigh": None, # pass in normalization values for 0.0 and 1.0 as list [low, high] (if not None, all following parameters ignored)
    "percentile": None, # pass in percentiles to use as list [perc_low, perc_high]
    "normalize": True, # run normalization (if False, all following parameters ignored)
    "norm3D": True, # compute normalization across entire z-stack rather than plane-by-plane in stitching mode.
    "sharpen_radius": 0, # sharpen image with high pass filter, recommended to be 1/4-1/8 diameter of cells in pixels
    "smooth_radius": 0, # smooth image with gaussian filter, recommended to be 1/4-1/8 diameter of cells in pixels
    "tile_norm_blocksize": 0, # compute normalization in tiles across image to brighten dark areas, to turn on set to window size in pixels (e.g. 100)
    "tile_norm_smooth3D": 1, # set amount of smoothing to apply to tile normalization in 3D
    "invert": False # invert image pixel intensity before running network. Defaults to False.
}
# TODO: Update to cellpose 4.0
def run_seg(cellpose_settings: dict[str, any], img: NDArray[T]) -> NDArray[T]:
    """
    Run segmentation on the image using Cellpose.
    Args:
        model_settings (dict): Settings for the Cellpose model.
        cp_settings (dict): Settings for the Cellpose segmentation.
        img (NDArray): The image to segment.
        do_denoise (bool): Whether to use denoising model or not. Default is True.
    Returns:
        NDArray: The segmented masks of the image as same dtype as the input image.
    """
    
    # Unpack settings
    mod_sets, eval_sets = _unpack_cellpose_settings(cellpose_settings)
    
    # Initialize Cellpose model
    model = _initialize_cellpose_model(mod_sets)
    
    # Run segmentation
    return _segment_image(img, eval_sets, model)


##################### Helper functions #####################
def _unpack_cellpose_settings(cellpose_settings: dict[str, any]) -> tuple[dict[str, any], dict[str, any]]:
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
    
    return mod_sets, eval_sets

def _initialize_cellpose_model(model_settings: dict[str, any])-> CellposeModel:
    """
    Initialize the Cellpose model, with lazy import to avoid unnecessary dependencies.
    """
    from cellpose.models import CellposeModel
    return CellposeModel(**model_settings)

def _segment_image(img: NDArray[T], eval_settings: dict, model: CellposeModel)-> NDArray[T]:
    """
    Run the segmentation on the image
    """
    return model.eval(img, **eval_settings)[0].astype(img.dtype)


if __name__ == "__main__":
    # Manual test
    
    from pathlib import Path
    from tifffile import imread, imwrite
    
    # Load image
    img_path = Path("/media/ben/Analysis/Python/Images/Image_tests/src_test/_z1_t10.tif")
    img = imread(img_path)
    
    # Load settings
    mod_sets = {"model_type": "cyto2",
                "restore_type": "denoise_cyto2",
                "gpu": True,}
    
    cp_sets = {"channels": None,
               "diameter": 60,
               "flow_threshold": 0.4,
               "cellprob_threshold": 0.0,
               "z_axis": None,
               "do_3D": False,
               "stitch_threshold": 0,}
    
    # Run segmentation
    masks = run_seg(mod_sets, cp_sets, img, True)
    
    # Save masks
    save_path = Path("/media/ben/Analysis/Python/Images/Image_tests/dst_test").joinpath(f"{img_path.name}_masks.tif")
    imwrite(save_path, masks.astype("uint16"))