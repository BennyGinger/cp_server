from pathlib import Path

import numpy as np
import tifffile as tiff



def generate_mask_path(img_file: str, dst_folder: str) -> Path:
    save_dir = Path(img_file).parent.parent.joinpath(dst_folder)
    save_dir.mkdir(exist_ok=True)
    mask_path = save_dir.joinpath(img_file.name.replace("refseg", "mask"))
    return mask_path

def extract_fov_id(img_file: str) -> str:
    """
    Extract the field of view (FOV) ID from the image file name.
    The FOV ID is expected to be the part of the file name before the first underscore.
    
    Args:
        img_file (str): The path to the image file.
        
    Returns:
        str: The extracted FOV ID.
    """
    return Path(img_file).stem.split("_")[0]


def save_mask(mask: np.ndarray, mask_path: str)-> None:
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
    
def save_img(img: np.ndarray, img_file: str)-> None:
    """
    Save the image to a TIFF file. The image is expected to be a 2D or 3D numpy array.
    Files are automatically compressed using zlib.
    Args:
        img (np.ndarray): The image array to save.
        img_file (str): The path where the image will be saved.
    """
    tiff.imwrite(img_file, img.astype("uint16"), compression='zlib')