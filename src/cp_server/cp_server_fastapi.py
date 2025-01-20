import json
import os
import signal
from fastapi import FastAPI, UploadFile, File, Query
import logging
from cellpose.denoise import CellposeDenoiseModel
from fastapi.responses import JSONResponse
import numpy as np
from dataclasses import field, dataclass

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

@dataclass
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
        # Denoise image has a bug and it requires channels list (even if default is set to None)
        if "channels" not in cp_settings:
            cp_settings['channels'] = [0, 0]
        
        elif cp_settings['channels'] is None:
            cp_settings['channels'] = [0, 0]
        
        # Run segmentation
        mask: list[np.ndarray] = self.model.eval(image, **cp_settings)[0]
        logging.info(f"Image segmented successfully: {len(mask)} masks created")
        
        return mask
        

# Initialize model
init_model = CellposeModel()

# Log model creation
logging.info("Default model created successfully")

# Check for Server Availability
@app.get("/health")
async def health()-> dict:
    return {"status": "ok"}

@app.post("/model/")
async def create_model(settings: dict)-> dict:
    """Expects a JSON payload with the following fields:
    - settings: Model settings to define the cellpose model"""
    
    # Initialize model
    settings = init_model.init_model(settings)
    
    # Log model update
    logging.info(f"Model updated successfully with settings: {settings}")
    
    return {"status": "Model created successfully"}

@app.post("/shutdown")
async def shutdown():
    def kill_server():
        os.kill(os.getpid(), signal.SIGINT)
    kill_server()
    return JSONResponse(content={"message": "Server shutting down..."})

# Segment an image
@app.post("/segment/")
async def segment(settings: str = Query(...), target_path: str = Query(...), img_file: UploadFile = File(...))-> dict:
    """Expects a JSON payload with the following fields:
    - image: list of lists representing the image
    - settings: Model and Cellpose settings to define the model and run the segmentation
    - target_path: Path where the processed image should be saved"""
    
    # Read image bytes
    img_bytes = await img_file.read()
    
    # Convert bytes to numpy array
    img_arr = np.reshape(np.frombuffer(img_bytes, dtype=np.uint8), (256, 256))
    print(f"Image shape: {img_arr.shape}")
    # Parse settings
    settings = json.loads(settings)
    
    # Run segmentation
    mask = init_model.segment(img_arr, settings)
    print(f"Mask shape: {mask.shape}")
    # Convert mask to bytes
    mask_bytes = mask.tobytes()
    
    logging.info("Image segmented successfully")
    return {"mask": mask_bytes, "target_path":target_path}


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