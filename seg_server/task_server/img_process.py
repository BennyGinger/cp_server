from pathlib import Path
import warnings

from cellpose.denoise import CellposeDenoiseModel
import tifffile as tiff

from seg_server.task_server import celery_logger

# Suppress FutureWarning messages from cellpose
warnings.filterwarnings("ignore", category=FutureWarning, module="cellpose")                

def cp_seg(src_dir: Path, dst_dir: Path, settings: dict):
    """Process images with Cellpose and save the masks"""
    
    # Initialize Cellpose model
    model_settings: dict = settings.get("model", {})
    model = CellposeDenoiseModel(**settings.get("model", {}))
    celery_logger.info("Cellpose model initialized")
    celery_logger.debug(f"{model_settings=}")
    
    # Run through the src_dir and process each image
    cp_settings: dict = settings.get("segmentation", {})
    celery_logger.debug(f"{cp_settings=}")
    for img_file in src_dir.rglob("*.tif"):
        img = tiff.imread(str(img_file))
        masks = model.eval(img, **settings.get("segmentation", {}))[0]
        
        # TODO: Check the logic of the naming convention
        # Save the masks
        save_path = dst_dir.joinpath(img_file.name)
        tiff.imwrite(str(save_path), masks.astype("uint16"))
    
    celery_logger.info("Processing complete")