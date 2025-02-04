from pathlib import Path

import numpy as np

from cp_server.task_server.celery_server import celery_app
from cp_server.task_server.tasks.bg_sub.bg_sub import apply_bg_sub
from cp_server.task_server.tasks.segementation.cp_seg import run_seg
from cp_server.task_server.tasks.saving.save_arrays import save_mask, save_img
from cp_server.task_server import celery_logger


@celery_app.task()
def remove_bg(img: np.ndarray, **kwargs)-> np.ndarray:
    """Apply background subtraction to the image"""
    bg_img = apply_bg_sub(img, **kwargs)
    save_img_task.delay(bg_img, kwargs["img_file"])
    return bg_img
    
@celery_app.task()
def segment(settings: dict, img: np.ndarray)-> np.ndarray:
    """Segment the image using Cellpose"""
    masks = run_seg(settings, img)
    save_masks_task.delay(masks, img, settings["dst_folder"], settings["key_label"])
    return run_seg(settings, img)

@celery_app.task()
def save_masks_task(masks: np.ndarray, img_file: Path, dst_folder: str, key_label: str)-> None:
    """Save the masks"""
    celery_logger.debug(f"Saving masks to {dst_folder}")
    return save_mask(masks, img_file, dst_folder, key_label)

@celery_app.task()
def save_img_task(img: np.ndarray, img_file: Path)-> None:
    """Save the image"""
    celery_logger.debug(f"Saving image to {img_file}")
    return save_img(img, img_file)

@celery_app.task()
def mock_task(src_dir: str, dest_dir: str)-> str:
    """Mock task for testing Celery worker with a long-running process"""
    
    celery_logger.info("Mock task started")
    celery_logger.debug(f"Source dir: {src_dir}")
    
    # Create mock text file
    reslt_path = Path(dest_dir).joinpath("mock_result.txt")
    celery_logger.debug(f"Result path: {reslt_path}")
    with open(reslt_path, "w") as file:
        
        for i, img in enumerate(Path(src_dir).iterdir()):
            if not img.suffix == ".tif":
                continue
            file.write(f"{i}-{img}\n")
        
    celery_logger.info("Mock task completed")
    return "Task finished successfully"

################# Main task #################
@celery_app.task()
def process_images()-> None:
    """Process images with background subtraction and segmentation"""
    
    celery_logger.info("Processing images")
    pass
    