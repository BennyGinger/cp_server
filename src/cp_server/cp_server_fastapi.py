from pathlib import Path
from fastapi import FastAPI
import logging
from cellpose.denoise import CellposeDenoiseModel
import numpy as np
from pydantic import BaseModel, ConfigDict
from dataclasses import field

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
    """Encapsulates the Cellpose model and provides methods to run segmentation"""
    
    model: CellposeDenoiseModel = field(init=False)
    
    def __post_init__(self)-> None:
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
    
    def segment(self, image: np.ndarray, cp_settings: dict)-> list[np.ndarray]:
        # Run segmentation
        mask: list[np.ndarray] = self.model.eval(image, **cp_settings)[0]
        logging.info(f"Image segmented successfully: {len(mask)} masks created")
        
        return mask
        
class SegmentedMask(BaseModel):
    """Encapsulates the segmented mask and target path"""
    mask: list[list]
    target_path: Path
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


# Initialize model
model = CellposeModel()
# Log model creation
logging.info("Model created successfully")

# Check for Server Availability
@app.get("/health")
async def health()-> dict:
    return {"status": "ok"}

@app.post("/model/")
async def create_model(settings: dict)-> dict:
    """Expects a JSON payload with the following fields:
    - settings: Model settings to define the cellpose model"""
    
    # Initialize model
    settings = model.init_model(settings)
    
    # Log model update
    logging.info(f"Model updated successfully with settings: {settings}")
    
    return {"status": "Model created successfully"}


# Segment an image
@app.post("/segment/")
async def segment(img_lst: list[list], settings: dict, target_path: Path)-> dict:
    """Expects a JSON payload with the following fields:
    - image: list of lists representing the image
    - settings: Model and Cellpose settings to define the model and run the segmentation
    - target_path: Path where the processed image should be saved"""
    
    # Convert image to numpy array
    img_arr = np.array(img_lst)
    
    # Run segmentation
    mask = model.segment(img_arr, settings)
    
    # Convert mask to list of lists
    mask = [m.tolist() for m in mask]
    logging.info("Image segmented successfully")
    return SegmentedMask(mask=mask, target_path=target_path)

if __name__ == "__main__":
    import httpx

    # Define the payload
    payload = {
        "gpu": True,
        "model_type": "cyto3",
        "pretrained_model": False
    }

    # Make a POST request to the /model/ endpoint
    response = httpx.post("http://127.0.0.1:8000/model/", json=payload)

    # Print the response
    print(response.status_code)
    print(response.json())