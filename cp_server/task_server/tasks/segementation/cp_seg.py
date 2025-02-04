import warnings

import numpy as np
from cellpose.denoise import CellposeDenoiseModel

from cp_server.task_server import celery_logger

# Suppress FutureWarning messages from cellpose
warnings.filterwarnings("ignore", category=FutureWarning, module="cellpose")                


def run_seg(settings: dict, img: np.ndarray)-> np.ndarray:
    # Initialize Cellpose model
    model_settings: dict = settings.get("model", {})
    model = CellposeDenoiseModel(**settings.get("model", {}))
    celery_logger.debug(f"{model_settings=}")
    
    # Run segmentation
    cp_settings: dict = settings.get("segmentation", {})
    celery_logger.debug(f"{cp_settings=}")
    
    masks = model.eval(img, **settings.get("segmentation", {}))[0]
    celery_logger.debug(f"{type(masks)=}", f"{masks.shape=}")
    return masks