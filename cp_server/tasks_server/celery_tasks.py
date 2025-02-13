from celery import chain, shared_task
import tifffile as tiff

from cp_server.tasks_server import celery_logger
from cp_server.tasks_server.tasks.bg_sub.bg_sub import apply_bg_sub
from cp_server.tasks_server.tasks.segementation.cp_seg import run_seg
from cp_server.tasks_server.tasks.saving.save_arrays import save_mask, save_img
from cp_server.tasks_server.utils import encode_ndarray_as_bytesb64, decode_bytesb64_to_array


PIPELINE_TYPE = {"refseg": "BioSensor Pipeline",
                "_z": "ImageAnalysis Pipeline",}


@shared_task(name="cp_server.task_server.celery_task.save_masks_task")
def save_masks_task(masks_b64: str, img_file: str, dst_folder: str, key_label: str)-> None:
    """Save the masks. Note that the image (ndarray) is encoded as a base64 string"""
    
    # Decode the masks
    masks = decode_bytesb64_to_array(masks_b64)
    celery_logger.debug(f"Decoding masks inside save_masks_task {masks.shape=} and {masks.dtype=}")
    return save_mask(masks, img_file, dst_folder, key_label)

@shared_task(name="cp_server.task_server.celery_task.save_img_task")
def save_img_task(img_b64: str, img_file: str)-> None:
    """Save the image. Note that the image (ndarray) is encoded as a base64 string"""
    
    # Decode the image
    img = decode_bytesb64_to_array(img_b64)
    celery_logger.debug(f"Decoding img inside save_img_task {img.shape=} and {img.dtype=}")
    return save_img(img, img_file)

@shared_task(name="cp_server.task_server.celery_task.remove_bg")
def remove_bg(img_b64: str, img_file: str, **kwargs)-> str:
    """Apply background subtraction to the image. Note that the image (ndarray) is encoded as a base64 string"""
    
    # Log the settings
    celery_logger.debug(f"Removing background from {img_file}")
    
    # Decode the image
    img = decode_bytesb64_to_array(img_b64)
    celery_logger.debug(f"Decoding img inside remove_bg {img.shape=} and {img.dtype=}")
    
    # Apply the background subtraction
    bg_img = apply_bg_sub(img, **kwargs)
    
    # Encode the image as a base64 string and save it in the background
    bg_img_b64 = encode_ndarray_as_bytesb64(bg_img)
    save_img_task.delay(bg_img_b64, img_file)
    return bg_img_b64
    
@shared_task(name="cp_server.task_server.celery_task.segment")
def segment(settings: dict, img_b64: str, img_file: str, dst_folder: str, key_label: str, do_denoise: bool=True)-> str:
    """Segment the image using Cellpose. Note that the image (ndarray) is encoded as a base64 string"""
    
    # Log the settings
    msg_settings = {**settings['model'], **settings['segmentation']}
    celery_logger.info(f"Segmenting image {img_file} with settings: {msg_settings}")
    
    # Decode the image
    img = decode_bytesb64_to_array(img_b64)
    celery_logger.debug(f"Decoding img inside segment {img.shape=} and {img.dtype=}")
    
    # Run the segmentation
    masks = run_seg(settings, img, do_denoise)
    celery_logger.debug(f"Created cp masks of {masks.shape=}")
    
    # Encode the mask and save it in the background
    celery_logger.info(f"Segmentation completed for {img_file}. Saving masks in {dst_folder}")
    masks_b64 = encode_ndarray_as_bytesb64(masks)
    save_masks_task.delay(masks_b64, img_file, dst_folder, key_label)
    return masks_b64

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
    
    # Encode the img as a base64 string
    img_b64 = encode_ndarray_as_bytesb64(img)

    # Create the workflow
    chain(remove_bg.s(img_b64, img_file, **kwargs),
          segment.s(settings, img_b64, img_file, dst_folder, key_label, do_denoise)).apply_async()
    celery_logger.info(f"Workflow created for {img_file}")
    return f"Processing images with workflow {img_file}"
