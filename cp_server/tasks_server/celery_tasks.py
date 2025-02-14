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
def save_masks_task(masks: np.ndarray, img_file: str, dst_folder: str, key_label: str)-> None:
    """Save the masks. Note that the image (ndarray) is encoded as a base64 string"""
    
    # Decode the masks
    celery_logger.debug(f"Decoding masks inside save_masks_task {masks.shape=} and {masks.dtype=}")
    return save_mask(masks, img_file, dst_folder, key_label)

@shared_task(name="cp_server.task_server.celery_task.save_img_task")
def save_img_task(img: np.ndarray, img_file: str)-> None:
    """Save the image. Note that the image (ndarray) is encoded as a base64 string"""
    
    # Decode the image
    celery_logger.debug(f"Decoding img inside save_img_task {img.shape=} and {img.dtype=}")
    return save_img(img, img_file)

@shared_task(name="cp_server.task_server.celery_task.remove_bg")
def remove_bg(img: np.ndarray, img_file: str, **kwargs)-> np.ndarray:
    """Apply background subtraction to the image. Note that the image (ndarray) is encoded as a base64 string"""
    
    # Log the settings
    celery_logger.debug(f"Removing background from {img_file}")
    
    # Decode the image
    celery_logger.debug(f"Decoding img inside remove_bg {img.shape=} and {img.dtype=}")
    
    # Apply the background subtraction
    bg_img = apply_bg_sub(img, **kwargs)
    
    # Encode the image as a base64 string and save it in the background
    save_img_task.delay(bg_img, img_file)
    return bg_img
    
@shared_task(name="cp_server.task_server.celery_task.segment")
def segment(img: np.ndarray, settings: dict, img_file: str, dst_folder: str, key_label: str, do_denoise: bool=True)-> np.ndarray:
    """Segment the image using Cellpose. Note that the image (ndarray) is encoded as a base64 string"""
    
    # Log the settings
    msg_settings = {**settings['model'], **settings['segmentation']}
    celery_logger.info(f"Segmenting image {img_file} with settings: {msg_settings}")
    
    # Decode the image
    celery_logger.debug(f"Decoding img inside segment {img.shape=} and {img.dtype=}")
    
    # Run the segmentation
    masks = run_seg(settings, img, do_denoise)
    celery_logger.debug(f"Created cp masks of {masks.shape=}")
    
    # Encode the mask and save it in the background
    celery_logger.info(f"Segmentation completed for {img_file}. Saving masks in {dst_folder}")
    save_masks_task.delay(masks, img_file, dst_folder, key_label)
    return masks

################# Main task #################
@shared_task(name="cp_server.task_server.celery_task.process_images")
def process_images(settings: dict[str, dict], img_file: str, dst_folder: str, key_label: str, do_denoise: bool=True, **kwargs)-> str:
    """Process images with background subtraction and segmentation. Note that the image (ndarray) is encoded as a base64 string"""
    
    # Starting point of the log
    celery_logger.info("------------------------")
    celery_logger.info(f"Processing image: {img_file} for the {PIPELINE_TYPE[key_label]}")
    celery_logger.info(f"Setting denoise to {do_denoise}")
    
    # load the image
    img = tiff.imread(img_file)
    celery_logger.debug(f"{img.shape=} and {img.dtype=}")

    # Create the workflow
    chain(remove_bg.s(img, img_file, **kwargs),
          segment.s(settings=settings, 
                    img_file=img_file, 
                    dst_folder=dst_folder, 
                    key_label=key_label, 
                    do_denoise=do_denoise)).apply_async()
    celery_logger.info(f"Workflow created for {img_file}")
    return f"Processing images with workflow {img_file}"
