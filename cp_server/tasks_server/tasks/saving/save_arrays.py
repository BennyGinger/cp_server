from pathlib import Path
import re

import numpy as np
import tifffile as tiff


IMG_MARKERS = ("refseg", "measure")
MASK_NAME = 'mask'

def generate_mask_path(img_file: str, dst_folder: str) -> Path:
    """
    Generate the path where the mask will be saved based on the image file name and destination folder.
    The assumption is that the coming file name is in the format '<FOVID>_refseg_[1-9].tif', so the mask will be saved as '<FOVID>_mask_[1-9].tif'.
    Args:
        img_file (str): The path to the image file.
        dst_folder (str): The destination folder where the mask will be saved (container path).
    Returns:
        Path: The path where the mask will be saved.
    """
    img_path = Path(img_file)
    
    # dst_folder is now a container path like "/data/A1_well/A1_masks"
    save_dir = Path(dst_folder)
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract the name of the image file and replace the marker with 'mask'
    name = img_path.name
    for marker in IMG_MARKERS:
        if f"_{marker}_" in name:
            name = name.replace(marker, MASK_NAME)
            break
    else:
        raise ValueError(f"No expected marker in {img_path.name!r}")
    return save_dir.joinpath(name)

def extract_fov_id(img_file: str) -> tuple[str, str]:
    """
    Extract the field of view (FOV) ID and timepoint from the image file name.
    The function can handle both mask files ('FOVID_mask_[1-9].tif') and input image files ('FOVID_refseg_[1-9].tif' or 'FOVID_measure_[1-9].tif').
    Args:
        img_file (str): The path to the image file.
    Returns:
        tuple[str, str]: A tuple containing the FOV ID and timepoint extracted from the image file name.
    """
    img_path = Path(img_file)
    
    # Try to extract from mask format first
    if "_mask_" in img_path.stem:
        extracted_items = img_path.stem.split("_mask_")
        if len(extracted_items) == 2:
            return (extracted_items[0], extracted_items[1])
    
    # Try to extract from image format (refseg, measure, etc.)
    # Look for pattern: FOVID_<type>_<timepoint>
    parts = img_path.stem.split("_")
    if len(parts) >= 3:
        # Last part should be timepoint, second-to-last should be type (refseg, measure, etc.)
        fov_id = "_".join(parts[:-2])  # Everything except last 2 parts
        timepoint = parts[-1]  # Last part
        return (fov_id, timepoint)
    
    raise ValueError(f"Could not extract FOV ID and timepoint from {img_path.name!r}")

def save_mask(mask: np.ndarray, mask_path: str) -> None:
    """
    Save the masks to a TIFF file. The masks are expected to be a 2D or 3D numpy array
    where each pixel value corresponds to a label of an object in the image.
    The function determines the appropriate data type for the mask based on the maximum label value. Files are automatically compressed using zlib.
    Args:
        masks (np.ndarray): The mask array to save.
        img_file (str): The path to the original image file, used to determine the save directory.
        dst_folder (str): The destination folder where the mask will be saved.
    """
    # Determine mask type based on the number of objects
    max_label = int(mask.max())
    if max_label <= np.iinfo(np.uint8).max:
        dtype = np.uint8
    elif max_label <= np.iinfo(np.uint16).max:
        dtype = np.uint16
    elif max_label <= np.iinfo(np.uint32).max:
        dtype = np.uint32
    else:
        raise ValueError(f"Too many objects in the mask: {max_label}. Cannot save as a mask.")
    
    # Save the masks
    tiff.imwrite(mask_path, mask.astype(dtype), compression='zlib')
    
def save_img(img: np.ndarray, img_file: str) -> None:
    """
    Save the image to a TIFF file. The image is expected to be a 2D or 3D numpy array.
    Files are automatically compressed using zlib.
    Args:
        img (np.ndarray): The image array to save.
        img_file (str): The path where the image will be saved.
    """
    tiff.imwrite(img_file, img.astype("uint16"), compression='zlib')