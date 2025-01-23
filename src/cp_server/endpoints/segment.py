
import base64
import logging
from cellpose.denoise import CellposeDenoiseModel
from fastapi import APIRouter, HTTPException, Query, Request, UploadFile, File
from cp_server.utils.segment_utils import decode_image, unpack_settings

# Initialize FastAPI router
router = APIRouter()

# Segment an image
@router.post("/segment")
async def segment(request: Request, settings: str = Query(...), img_shape: str = Query(...), target_path: str = Query(...), img_file: UploadFile = File(...))-> dict:
    """Expects a JSON payload with the following fields:
    - settings (str): Cellpose eval settings to run the segmentation
    - target_path (str): Path where the processed image should be saved
    - image (bytes): image to be segmented
    
    Returns -> dict:
    - mask (bytes): Segmented image mask
    - target_path (str): Path where the processed image should be saved
    """
    try:
        # Read image bytes
        img_bytes = await img_file.read()
        
        # Convert bytes to numpy array
        img_arr = decode_image(img_bytes, img_shape)
        print(f"Image shape: {img_arr.shape}")
        # Log image reading
        logging.info(f"Image read successfully with shape {img_arr.shape}")
        
    except Exception as e:
        logging.error(f"Failed to read image: {e}")
        raise HTTPException(status_code=500, detail=f"Image reading failed: {e}")
    
    # Parse settings
    cp_eval_settings = unpack_settings(settings)
    
    # Load the model
    cp_model: CellposeDenoiseModel = request.app.state.cp_model
    
    try:
        # Run segmentation
        mask = cp_model.eval(img_arr, **cp_eval_settings)[0]
        print(f"Mask shape: {mask.shape}")
        # Convert mask to bytes
        mask_bytes = mask.tobytes()
        
        # Encode mask bytes to base64 string
        mask_base64 = base64.b64encode(mask_bytes).decode('utf-8')
        
        logging.info(f"Image segmented successfully with mask shape {mask.shape}")
        return {"mask": mask_base64, "target_path":target_path}
    except Exception as e:
        logging.error(f"Failed to segment image: {e}")
        raise HTTPException(status_code=500, detail=f"Segment image failed: {e}")