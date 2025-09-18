from celery import shared_task
from typing import Union, List
from tifffile import imread

from concurrent.futures import ThreadPoolExecutor
from functools import partial

from cp_server.tasks_server import get_logger
from cp_server.tasks_server.tasks.bg_sub.bg_sub import apply_bg_sub
from cp_server.tasks_server.tasks.saving.save_arrays import save_img

logger = get_logger(__name__)

def _process_single_bg(img_path: str, sigma: float, size: int) -> str:
    logger.debug(f"Removing background from {img_path}")
    img = imread(img_path)
    logger.debug(f"{img.shape=} and {img.dtype=}")
    bg_img = apply_bg_sub(img, sigma, size)
    save_img(bg_img, img_path)
    logger.info(f"Background-subtracted image overwritten at {img_path}")
    return str(img_path)

@shared_task(name="cp_server.tasks_server.tasks.bg_sub.remove_bg")
def remove_bg(img_path: Union[str, List[str]], sigma: float, size: int) -> Union[str, List[str]]:
    """
    Apply background subtraction to one or more images, save the result(s), and return the file path(s).
    """
    if isinstance(img_path, list):
        logger.info(f"Processing {len(img_path)} images in parallel for background subtraction.")
        with ThreadPoolExecutor() as executor:
            func = partial(_process_single_bg, sigma=sigma, size=size)
            results = list(executor.map(func, img_path))
        return results
    else:
        return _process_single_bg(img_path, sigma, size)

