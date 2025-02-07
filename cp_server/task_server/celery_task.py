from pathlib import Path

from celery import chain
import numpy as np
import tifffile as tiff

from cp_server.task_server import celery_logger
from cp_server.task_server.celery_app import celery_app
from cp_server.task_server.tasks.bg_sub.bg_sub import apply_bg_sub
from cp_server.task_server.tasks.segementation.cp_seg import run_seg
from cp_server.task_server.tasks.saving.save_arrays import save_mask, save_img


PIPELINE_TYPE = {"refseg": "BioSensor Pipeline",
                "_z": "ImageAnalysis Pipeline",}


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
def remove_bg(img: np.ndarray, img_file: Path, **kwargs)-> np.ndarray:
    """Apply background subtraction to the image"""
    bg_img = apply_bg_sub(img, **kwargs)
    save_img_task.delay(bg_img, img_file)
    return bg_img
    
@celery_app.task()
def segment(settings: dict, img: np.ndarray, img_file: Path, dst_folder: str, key_label: str, do_denoise: bool=True)-> np.ndarray:
    """Segment the image using Cellpose"""
    
    # Log the settings
    msg_settings = {**settings['model'], **settings['segmentation']}
    celery_logger.info(f"Segmenting image {img_file} with settings: {msg_settings}")
    
    # Run the segmentation
    masks = run_seg(settings, img, do_denoise)
    celery_logger.debug(f"{masks.shape=}")
    
    # Save the masks in the background
    celery_logger.info(f"Segmentation completed for {img_file}. Saving masks in {dst_folder}")
    save_masks_task.delay(masks, img_file, dst_folder, key_label)
    return masks

################# Main task #################
@celery_app.task()
def process_images(settings: dict[str, dict], img_file: Path, dst_folder: str, key_label: str, do_denoise: bool=True, **kwargs)-> str:
    """Process images with background subtraction and segmentation"""
    # Starting point of the log
    celery_logger.info("------------------------")
    celery_logger.info(f"Processing image: {img_file} for the {PIPELINE_TYPE[key_label]}")
    celery_logger.info(f"Setting denoise to {do_denoise}")
    
    # load the image
    img = tiff.imread(img_file)
    celery_logger.debug(f"{img.shape=}")

    # Create the workflow
    chain(remove_bg.s(img, img_file, **kwargs),
          segment.s(settings, img, img_file, dst_folder, key_label, do_denoise)).apply_async()
    celery_logger.info(f"Workflow created for {img_file}")
    return f"Processing images with workflow {img_file}"
