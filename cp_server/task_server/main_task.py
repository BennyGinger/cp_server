from pathlib import Path

import tifffile as tiff

from cp_server.task_server import celery_logger
from cp_server.task_server.tasks.segementation.cp_seg import run_seg
from cp_server.task_server.tasks.bg_sub.bg_sub import apply_bg_sub
from cp_server.task_server.tasks.saving.save_arrays import save_mask



def seg_imgs(mnt_dir: Path, src_folder: str, dst_folder: str, settings: dict, key_label: str)-> None:
    """Process images with Cellpose and save the masks. Key_label is used to identify the pipeline, refseg = A1, _z = ImageAnalysis"""
    
    celery_logger.info(f"Processing images in {mnt_dir} in all {src_folder} subfolders")
    for img_file in mnt_dir.rglob("*.tif"):
        # Check that parent dir has the same name as the src_folder
        if img_file.parent.name != src_folder:
            continue
        
        # Ignore the control and measure images
        if key_label not in img_file.name:
            continue
        
        # Load the image
        img = tiff.imread(str(img_file))
        
        # Process the image
        img = apply_bg_sub(img)
        
        masks = run_seg(settings, img)
        
        # Save the masks
        save_mask(masks, img_file, dst_folder, key_label)
    
