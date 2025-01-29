from pathlib import Path
import warnings
from celery import Celery
from cellpose.denoise import CellposeDenoiseModel
import tifffile as tiff
from . import logger  # Import global logger

# Suppress FutureWarning messages from cellpose
warnings.filterwarnings("ignore", category=FutureWarning, module="cellpose")

# Configure Celery
celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    broker_connection_retry_on_startup=True
)

@celery_app.task(bind=True)
def process_images(self, src_dir: str, dst_dir: str, settings: dict, image_name: str):
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
            logger.info(f"Processing complete for {image_name}")
        else:
            logger.warning(f"Image {image_name} not found or invalid format")
    except Exception as e:
        logger.error(f"Error processing image {image_name}: {e}")
