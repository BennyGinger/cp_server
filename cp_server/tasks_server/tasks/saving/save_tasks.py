from celery import shared_task
import numpy as np

from cp_server.tasks_server import get_logger
from cp_server.tasks_server.tasks.saving.save_arrays import save_img


logger = get_logger(__name__)

@shared_task(name="cp_server.tasks_server.tasks.saving.save_img_task")
def save_img_task(img: np.ndarray, 
                  img_path: str,
                  ) -> None:
    """
    Save the image. Note that the image (ndarray) is encoded as a base64 string
    """
    # Decode the image
    logger.debug(f"Decoding img inside save_img_task {img.shape=} and {img.dtype=}")
    return save_img(img, img_path)