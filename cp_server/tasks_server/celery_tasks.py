from pathlib import Path

from celery import chain, shared_task
import numpy as np
import tifffile as tiff

from cp_server.tasks_server import celery_logger
from cp_server.tasks_server.tasks.bg_sub.bg_sub import apply_bg_sub
from cp_server.tasks_server.tasks.segementation.cp_seg import run_seg
from cp_server.tasks_server.tasks.saving.save_arrays import save_mask, save_img


PIPELINE_TYPE = {"refseg": "BioSensor Pipeline",
                "_z": "ImageAnalysis Pipeline",}


@shared_task(name="cp_server.task_server.celery_task.save_masks_task")
def save_masks_task(masks: np.ndarray, img_file: Path, dst_folder: str, key_label: str)-> None:
    """Save the masks"""
    celery_logger.debug(f"Saving masks to {dst_folder}")
    return save_mask(masks, img_file, dst_folder, key_label)

@shared_task(name="cp_server.task_server.celery_task.save_img_task")
def save_img_task(img: np.ndarray, img_file: Path)-> None:
    """Save the image"""
    celery_logger.debug(f"Saving image to {img_file}")
    return save_img(img, img_file)

@shared_task(name="cp_server.task_server.celery_task.remove_bg")
def remove_bg(img: np.ndarray, img_file: Path, **kwargs)-> list:
    """Apply background subtraction to the image"""
    bg_img = apply_bg_sub(img, **kwargs)
    save_img_task.delay(bg_img, img_file)
    return bg_img.tolist()
    
@shared_task(name="cp_server.task_server.celery_task.segment")
def segment(settings: dict, img: list, img_file: Path, dst_folder: str, key_label: str, do_denoise: bool=True)-> np.ndarray:
    """Segment the image using Cellpose. Note that the image is passed as a list to be compatible with Celery serialization"""
    
    # Log the settings
    msg_settings = {**settings['model'], **settings['segmentation']}
    celery_logger.info(f"Segmenting image {img_file} with settings: {msg_settings}")
    
    # Run the segmentation
    masks = run_seg(settings, np.array(img), do_denoise)
    celery_logger.debug(f"{masks.shape=}")
    
    # Save the masks in the background
    celery_logger.info(f"Segmentation completed for {img_file}. Saving masks in {dst_folder}")
    save_masks_task.delay(masks, img_file, dst_folder, key_label)
    return masks

################# Main task #################
@shared_task(name="cp_server.task_server.celery_task.process_images")
def process_images(settings: dict[str, dict], img_file: str, dst_folder: str, key_label: str, do_denoise: bool=True, **kwargs)-> str:
    """Process images with background subtraction and segmentation"""
    # Starting point of the log
    celery_logger.info("------------------------")
    celery_logger.info(f"Processing image: {img_file} for the {PIPELINE_TYPE[key_label]}")
    celery_logger.info(f"Setting denoise to {do_denoise}")
    
    # load the image
    img = tiff.imread(img_file)
    celery_logger.debug(f"{img.shape=}")

    # Create the workflow
    chain(remove_bg.s(img, Path(img_file), **kwargs),
          segment.s(settings, img, Path(img_file), dst_folder, key_label, do_denoise)).apply_async()
    celery_logger.info(f"Workflow created for {img_file}")
    return f"Processing images with workflow {img_file}"
