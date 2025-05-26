import logging
from pathlib import Path
import os
from urllib.parse import urlparse

import redis
from celery import chain, shared_task
import numpy as np
import tifffile as tiff

from cp_server.tasks_server.tasks.bg_sub.bg_sub import apply_bg_sub
from cp_server.tasks_server.tasks.segementation.cp_seg import run_seg
from cp_server.tasks_server.tasks.saving.save_arrays import generate_mask_path, save_mask, save_img
from cp_server.tasks_server.tasks.track.track import track_masks


# Initialize Redis client from CELERY_BROKER_URL environment variable
url = os.environ["CELERY_BROKER_URL"]  # e.g. redis://redis:6379/0
parse_url = urlparse(url)
redis_client = redis.Redis(host=parse_url.hostname, port=parse_url.port, db=int(parse_url.path.lstrip("/")))

# Setup logging
celery_logger = logging.getLogger(__name__)


###########################
# Orchestration tasks     #
###########################
@shared_task(name="cp_server.tasks_server.celery_tasks.mark_one_done")
def mark_one_done() -> None:
    """
    Celery callback: decrement the pending counter; if zero, fire final task.
    """
    remaining = redis_client.decr("pending_tracks")
    celery_logger.info(f"Tracks remaining: {remaining}")
    if remaining == 0:
        all_tracks_finished.delay()

@shared_task(name="cp_server.tasks_server.celery_tasks.all_tracks_finished")
def all_tracks_finished() -> str:
    """
    Runs once when the last track_cells completes for this run_id.
    """
    celery_logger.info("All tracking done for all FOVs")
    redis_client.delete("pending_tracks")  # Clear the pending counter
    return "All tracks finished"  

###########################
# File processing tasks   #
###########################

@shared_task(name="cp_server.tasks_server.celery_tasks.save_masks_task")
def save_masks_task(mask: np.ndarray, 
                    mask_path: str,
                    ) -> None:
    """
    Save the masks. Note that the image (ndarray) is encoded as a base64 string
    """
    # Decode the masks
    celery_logger.debug(f"Decoding masks inside save_masks_task {mask.shape=} and {mask.dtype=}")
    return save_mask(mask, mask_path)

@shared_task(name="cp_server.tasks_server.celery_tasks.save_img_task")
def save_img_task(img: np.ndarray, 
                  img_path: str,
                  ) -> None:
    """
    Save the image. Note that the image (ndarray) is encoded as a base64 string
    """
    # Decode the image
    celery_logger.debug(f"Decoding img inside save_img_task {img.shape=} and {img.dtype=}")
    return save_img(img, img_path)

@shared_task(name="cp_server.tasks_server.celery_tasks.remove_bg")
def remove_bg(img: np.ndarray, 
              img_path: str, 
              sigma: float, 
              size: int,
              ) -> np.ndarray:
    """
    Apply background subtraction to the image. Note that the image (ndarray) is encoded as a base64 string
    """
    # Debug log the image file and settings
    celery_logger.debug(f"Removing background from {img_path}")
    celery_logger.debug(f"Decoding img inside remove_bg {img.shape=} and {img.dtype=}")
    
    # Apply the background subtraction
    bg_img = apply_bg_sub(img, sigma, size)
    
    # Encode the image as a base64 string and save it in the background
    save_img_task.delay(bg_img, img_path)
    return bg_img
    
@shared_task(name="cp_server.tasks_server.celery_tasks.segment")
def segment(img: np.ndarray, 
            mod_settings: dict[str, any],
            cp_settings: dict[str, any],
            img_file: str, 
            dst_folder: str,
            round: int,
            stitch_threshold: float,
            do_denoise: bool, 
            ) -> None:
    """
    Segment the image using Cellpose. Note that the image (ndarray) is encoded as a base64 string
    """
    # Log the settings
    celery_logger.info(f"Initializing segmentation for {img_file} with settings: {mod_settings}")
    celery_logger.info(f"Segmentation parameters are: {cp_settings}")
    celery_logger.debug(f"Decoding img inside segment {img.shape=} and {img.dtype=}")
    
    # Run the segmentation
    mask = run_seg(mod_settings, cp_settings, img, do_denoise)
    celery_logger.debug(f"Created cp masks of {mask.shape=}")
    
    # Encode the mask and save it in the background
    celery_logger.info(f"Segmentation completed for {img_file}. Saving masks in {dst_folder}")
    mask_path = generate_mask_path(img_file, dst_folder)
    save_masks_task.delay(mask, str(mask_path))
    
    # Extract fovID and timepoint from the image file name
    fov_id, time_id = mask_path.stem.split("_mask_") # On the assumption that files look like: "fovID_mask_1.tif"
    celery_logger.debug(f"Extracted fov_id: {fov_id} and time_id: {time_id} from {mask_path}")
    
    # Register the run_id and fov_id in Redis
    hkey = f"masks:{fov_id}"
    redis_client.hset(hkey, time_id, str(mask_path))
    celery_logger.info(f"Stored mask for {fov_id} time {time_id}")
    
    # Round 2: pair and trigger tracking
    if round == 2 and redis_client.hlen(hkey) == 2:
        celery_logger.info(f"Found 2 masks for {fov_id}, triggering tracking")
        paths: list[str] = [p.decode() for p in redis_client.hvals(hkey)]
        celery_logger.debug(f"Paths to track: {paths}")
        redis_client.delete(hkey)  # Clear the hash for this fov_id
        
        # Trigger the tracking task
        track_cells.apply_async(
            args=[paths, stitch_threshold],
            link=mark_one_done.s())
    
@shared_task(name="cp_server.tasks_server.celery_tasks.track_cells")
def track_cells(mask_paths: list[str], 
                stitch_threshold: float,
                ) -> None:
    """
    Task to track cells in a time series of images. Masks are stitched together based on a threshold for IOU (Intersection Over Union).
    Masks are then relabeled sequentially to ensure unique labels across the time series.
    """
    
    # Log
    celery_logger.info(f"Tracking cells in {len(mask_paths)} images with stitch_threshold {stitch_threshold}")
    
    # Load the stack of masks
    masks = [tiff.imread(path) for path in mask_paths]
    masks = np.array(masks).astype(np.uint16)
    celery_logger.debug(f"Loaded masks of shape {masks.shape=}")
    
    # Track the cells and trim the masks
    stitched_masks = track_masks(masks, stitch_threshold)
    celery_logger.debug(f"Stitched masks of shape {stitched_masks.shape=}")
    
    # Overwrite the original masks with the stitched ones
    for mask, path in zip(stitched_masks, mask_paths):
        save_masks_task.delay(mask, path)


################# Main tasks #################
@shared_task(name="cp_server.tasks_server.celery_tasks.process_images")
def process_images(mod_settings: dict[str, any],
                   cp_settings: dict[str, any], 
                   img_file: str, 
                   dst_folder: str, 
                   round: int,
                   total_fovs: int=None,
                   do_denoise: bool=True,
                   stitch_threshold: float=0.25, 
                   sigma: float=0.0, 
                   size: int=7,
                   ) -> str:
    """
    Process images with background subtraction and segmentation. Note that the image (ndarray) is encoded as a base64 string.
    Args:
        mod_settings (dict): Model settings for Cellpose.
        cp_settings (dict): Segmentation settings for Cellpose.
        img_file (str): Path to the image file to be processed.
        dst_folder (str): Destination folder where the masks will be saved.
        round (int): The current round of processing (1 or 2).
        total_fovs (int, optional): Total number of fields of view for tracking. Defaults to None.
        do_denoise (bool, optional): Whether to apply denoising. Defaults to True.
        stitch_threshold (float, optional): Threshold for stitching masks. Defaults to 0.25.
        sigma (float, optional): Sigma value for background subtraction. Defaults to 0.0.
        size (int, optional): Size parameter for background subtraction. Defaults to 7."""
    
    # Starting point of the log
    celery_logger.info(f"Received image file: {img_file}")
    celery_logger.info(f"Setting denoise to {do_denoise}, round {round}")
    
    # Initialize tracking counter at start of round 2
    if round == 2 and total_fovs:
        redis_client.setnx("pending_tracks", total_fovs)
        celery_logger.info(f"Initialized pending counter to {total_fovs}")
    
    # load the image
    img = tiff.imread(img_file)
    celery_logger.debug(f"{img.shape=} and {img.dtype=}")

    # Create the workflow
    chain(remove_bg.s(
                img=img, 
                img_path=img_file, 
                sigma=sigma, 
                size=size),
          segment.s(
                mod_settings=mod_settings,
                cp_settings=cp_settings,
                img_file=img_file,
                dst_folder=dst_folder, 
                round=round,
                stitch_threshold=stitch_threshold,
                do_denoise=do_denoise)
          ).apply_async()
    celery_logger.info(f"Workflow created for {img_file}")
    return f"Image {img_file} was sent to be segmented"
