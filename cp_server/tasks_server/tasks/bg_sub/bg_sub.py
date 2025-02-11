import numpy as np
from smo import SMO


def apply_bg_sub(img: np.ndarray, sigma: float=0.0, size: int=7)-> np.ndarray:
    """Apply background subtraction to the image"""
    
    smo = SMO(shape=img.shape, sigma=sigma, size=size)
    
    bg_img = smo.bg_corrected(img)
    # Reset neg val to 0
    bg_img[bg_img<0] = 0
    
    return bg_img.astype(img.dtype)