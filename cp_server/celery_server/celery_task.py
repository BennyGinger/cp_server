import warnings
from pathlib import Path
import logging

from cellpose.denoise import CellposeDenoiseModel
import tifffile as tiff
from celery.signals import after_setup_logger

from .celery_server import celery_app
from cp_server.utils import find_project_root



# Suppress FutureWarning messages from cellpose
warnings.filterwarnings("ignore", category=FutureWarning, module="cellpose")

# Configure Celery logging
celery_logger = logging.getLogger(__name__)

@after_setup_logger.connect
def setup_loggers(logger: logging.Logger, *args, **kwargs)-> None:
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    log_path = find_project_root().joinpath("logs","celery.log")
    
    # FileHandler
    fh = logging.FileHandler("/media/ben/Analysis/Python/cp_server/logs/celery.log")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # StreamHandler
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    # Set the logging level
    logger.setLevel(logging.DEBUG)
    
    # Disable Module logging
    celery_mod_logger = logging.getLogger("celery")
    celery_mod_logger.disabled = True
    kombu_logger = logging.getLogger('kombu')
    kombu_logger.setLevel(logging.WARNING)
    
    # Append an empty line at the beginning of the log file
    with open(log_path, "a") as f:
        f.write("\n")

@celery_app.task(bind=True)
def process_images(self, src_dir: str, dst_dir: str, settings: dict, image_name: str)-> None:
    """Background task to process images with Cellpose"""
    try:
                
        # Initialize Cellpose model
        model = CellposeDenoiseModel(model_type=settings.get("model_type", "cyto"))
        
        img_path = Path(src_dir).joinpath(image_name)
        if img_path.exists() and img_path.suffix == ".tif":
            img = tiff.imread(str(img_path))
            masks = model.eval(img, **settings.get("segmentation", {}))[0]
            
            # Save the masks
            save_path = Path(dst_dir).joinpath(f"mask_{image_name}.tif")
            tiff.imwrite(str(save_path), masks)
            celery_logger.info(f"Processing complete for {image_name}")
        else:
            celery_logger.warning(f"Image {image_name} not found or invalid format")
    except Exception as e:
        celery_logger.error(f"Error processing image {image_name}: {e}")

@celery_app.task(bind=True)
def mock_task(self, src_dir: str, dest_dir: str)-> str:
    """Mock task for testing Celery worker with a long-running process"""
    
    celery_logger.info("Mock task started")
    celery_logger.debug(f"Source dir: {src_dir}")
    
    # Create mock text file
    reslt_path = Path(dest_dir).joinpath("mock_result.txt")
    celery_logger.debug(f"Result path: {reslt_path}")
    with open(reslt_path, "w") as file:
        
        for i, img in enumerate(Path(src_dir).iterdir()):
            if not img.suffix == ".tif":
                continue
            file.write(f"{i}-{img}\n")
        
    celery_logger.info("Mock task completed")
    return "Task finished successfully"
    
    