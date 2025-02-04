from pathlib import Path

import numpy as np
import tifffile as tiff


def save_mask(masks: np.ndarray, img_file: Path, dst_folder: str, key_label: str)-> None:
    # Save the masks
    save_dir = img_file.parent.parent.joinpath(dst_folder)
    save_dir.mkdir(exist_ok=True)
    match key_label:
        case "refseg":
            save_path = save_dir.joinpath(img_file.name.replace("refseg", "mask"))
        case "_z":
            save_path = save_dir.joinpath(img_file.name)
        
    tiff.imwrite(str(save_path), masks.astype("uint16"))
    
def save_img(img: np.ndarray, img_file: Path)-> None:
    tiff.imwrite(str(img_file), img.astype("uint16"))