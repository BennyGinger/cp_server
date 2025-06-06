from celery import shared_task
import numpy as np

from cp_server.tasks_server import get_logger
from cp_server.tasks_server.tasks.bg_sub.bg_sub import apply_bg_sub
from cp_server.tasks_server.tasks.saving.save_tasks import save_img_task



logger = get_logger(__name__)

@shared_task(name="cp_server.tasks_server.tasks.bg_sub.remove_bg")
def remove_bg(img: np.ndarray, 
              img_path: str, 
              sigma: float, 
              size: int,
              ) -> np.ndarray:
    """
    Apply background subtraction to the image. Note that the image (ndarray) is encoded as a base64 string
    """
    # Debug log the image file and settings
    logger.debug(f"Removing background from {img_path}")
    logger.debug(f"Decoding img inside remove_bg {img.shape=} and {img.dtype=}")
    
    # Apply the background subtraction
    bg_img = apply_bg_sub(img, sigma, size)
    
    # Encode the image as a base64 string and save it in the background
    save_img_task.delay(bg_img, img_path)
    return bg_img