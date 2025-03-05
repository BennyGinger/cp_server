from celery import chain, shared_task
import numpy as np
import tifffile as tiff

from cp_server.tasks_server import celery_logger
from cp_server.tasks_server.tasks.bg_sub.bg_sub import apply_bg_sub
from cp_server.tasks_server.tasks.segementation.cp_seg import run_seg
from cp_server.tasks_server.tasks.saving.save_arrays import save_mask, save_img
from cp_server.tasks_server.tasks.track.track import track_masks


PIPELINE_TYPE = {"refseg": "BioSensor Pipeline",
                "_z": "ImageAnalysis Pipeline",}


@shared_task(name="cp_server.tasks_server.celery_tasks.save_masks_task")
def save_masks_task(masks: np.ndarray, img_file: str, dst_folder: str, key_label: str)-> None:
    """Save the masks. Note that the image (ndarray) is encoded as a base64 string"""
    
    # Decode the masks
    celery_logger.debug(f"Decoding masks inside save_masks_task {masks.shape=} and {masks.dtype=}")
    return save_mask(masks, img_file, dst_folder, key_label)

@shared_task(name="cp_server.tasks_server.celery_tasks.save_img_task")
def save_img_task(img: np.ndarray, img_file: str)-> None:
    """Save the image. Note that the image (ndarray) is encoded as a base64 string"""
    
    # Decode the image
    celery_logger.debug(f"Decoding img inside save_img_task {img.shape=} and {img.dtype=}")
    return save_img(img, img_file)

@shared_task(name="cp_server.tasks_server.celery_tasks.remove_bg")
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
    
@shared_task(name="cp_server.tasks_server.celery_tasks.segment")
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


################# Main tasks #################
@shared_task(name="cp_server.tasks_server.celery_tasks.process_images")
def process_images(settings: dict[str, dict], img_file: str, dst_folder: str, key_label: str, do_denoise: bool=True, **kwargs)-> str:
    """Process images with background subtraction and segmentation. Note that the image (ndarray) is encoded as a base64 string"""
    
    # Starting point of the log
    celery_logger.info(f"Received image file: {img_file} for the {PIPELINE_TYPE[key_label]}")
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
    return f"Image {img_file} was sent to be segmented"

@shared_task(name="cp_server.tasks_server.celery_tasks.track_cells")
def track_cells(img_files: list[str], stitch_threshold: float)-> str:
    """Task to track cells in a time series of images"""
    
    # Log
    celery_logger.info(f"Tracking cells in {len(img_files)} images with stitch_threshold {stitch_threshold}")
    
    # Load the stack of masks
    masks = [tiff.imread(img_file) for img_file in img_files]
    masks = np.array(masks).astype(np.uint16)
    celery_logger.debug(f"Loaded masks of shape {masks.shape=}")
    
    # Track the cells and trim the masks
    stitched_masks = track_masks(masks, stitch_threshold)
    celery_logger.debug(f"Stitched masks of shape {stitched_masks.shape=}")
    
    # Save the stitched masks
    for i, img_file in enumerate(img_files):
        save_masks_task.delay(stitched_masks[i], img_file)
    return f"Images starting with {img_files[0]} were sent to be tracked"