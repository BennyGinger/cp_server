from pathlib import Path
from fastapi import FastAPI
import logging
from cellpose.denoise import CellposeDenoiseModel
import numpy as np
from pydantic import BaseModel, Field

# Default cellpose settings
MODEL_SETTINGS = {'gpu':True,
                  'model_type': 'cyto2',
                  'pretrained_model':False}


# Initialize FastAPI app
app = FastAPI()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set the minimum logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log message format
    handlers=[
        logging.FileHandler(".log"),  # Save logs to a file named 'app.log'
        logging.StreamHandler(),  # Also output logs to the console
    ])

class CellposeModel():
    model: CellposeDenoiseModel = Field(default=None)
    
    
    def __init__(self)-> None:
        # Determine model settings
        model_settings = self.init_model(MODEL_SETTINGS)
        
        # Initialize model
        self.model = CellposeDenoiseModel(**model_settings)
    
    def init_model(self, model_settings)-> dict:
        # Update model settings
        for k, v in model_settings.items():
            if k in MODEL_SETTINGS:
                model_settings[k] = v
        
        # Set restore type
        match model_settings['model_type']:
            case "cyto2":
                model_settings['restore_type'] = "denoise_cyto2"
            case "cyto3":
                model_settings['restore_type'] = "denoise_cyto3"
            case _:
                model_settings['restore_type'] = "denoise_cyto2"
        return model_settings
      
    def segment(self, image: np.ndarray | list[np.ndarray], cp_settings: dict)-> np.ndarray | list[np.ndarray]:
        # Run segmentation
        return self.model.eval(image, **cp_settings)[0]

class SegmentedMask(BaseModel):
    mask: np.ndarray | list[np.ndarray]
    target_path: Path
    
    class Config:
        arbitrary_types_allowed = True

# Initialize model
model = CellposeModel()


# Check for Server Availability
@app.get("/health")
async def health()-> dict:
    return {"status": "ok"}

@app.post("/model/")
async def create_model(settings: dict)-> dict:
    """Expects a JSON payload with the following fields:
    - settings: Model settings to define the cellpose model"""
    
    # Initialize model
    model.init_model(settings)
    
    # Log model creation
    logging.info("Model created successfully")
    
    return {"status": "Model created successfully"}


# Segment an image
@app.post("/segment/")
async def segment(image: np.ndarray | list[np.ndarray], settings: dict, target_path: Path)-> dict:
    """Expects a JSON payload with the following fields:
    - image: Base64 encoded image data
    - settings: Model and Cellpose settings to define the model and run the segmentation
    - target_path: Path where the processed image should be saved"""
    
    # Run segmentation
    mask = model.segment(image, settings)
    
    # Log segmentation
    logging.info("Image segmented successfully")
    return SegmentedMask(mask=mask, target_path=target_path)

