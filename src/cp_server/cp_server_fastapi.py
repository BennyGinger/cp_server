from fastapi import FastAPI
import logging
from cellpose.denoise import CellposeDenoiseModel
import numpy as np
from pydantic import BaseModel
from dataclasses import field

# Default cellpose settings
MODEL_SETTINGS = {'gpu':True,
                  'model_type': 'cyto2',
                  'pretrained_model':False,
                  'diam_mean':30.}

CELLPOSE_EVAL = {'batch_size':8,
                 'resample':True,
                 'channels':[0,0],
                 'channel_axis':None,
                 'z_axis':None,
                 'normalize':True,
                 'invert':False,
                 'rescale':None,
                 'diameter':60.,
                 'flow_threshold':0.4,
                 'cellprob_threshold':0.,
                 'do_3D':False,
                 'anisotropy':None,
                 'stitch_threshold':0.,
                 'min_size':15,
                 'niter':None,
                 'augment':False,
                 'tile':True,
                 'tile_overlap':0.1,
                 'bsize':224,
                 'interp':True,
                 'compute_masks':True,
                 'progress':None}


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set the minimum logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log message format
    handlers=[
        logging.FileHandler(".log"),  # Save logs to a file named 'app.log'
        logging.StreamHandler(),  # Also output logs to the console
    ])

class CellposeModel(BaseModel):
    model_settings: dict
    model: CellposeDenoiseModel = field(init=False)
    cp_settings: dict = field(init=False)
    
    
    def __post_init__(self, model_settings: dict)-> None:
        self.model_settings = MODEL_SETTINGS
        
        # Update model settings
        for k, v in model_settings.items():
            if k in MODEL_SETTINGS:
                self.model_settings[k] = v
        
        # Set restore type
        match self.model_settings['model_type']:
            case "cyto2":
                self.model_settings['restore_type'] = "denoise_cyto2"
            case "cyto3":
                self.model_settings['restore_type'] = "denoise_cyto3"
            case _:
                self.model_settings['restore_type'] = "denoise_cyto2"
        
        # Initialize model
        self.model = CellposeDenoiseModel(**self.model_settings)
        
    def segment(self, image: np.ndarray | list[np.ndarray], cp_settings: dict)-> np.ndarray | list[np.ndarray]:
        # Update settings
        for k, v in cp_settings.items():
            if k in CELLPOSE_EVAL:
                self.cp_settings[k] = v
        
        # Run segmentation
        return self.model.eval(image, **self.cp_settings)[0]

# Initialize FastAPI app
app = FastAPI()
    
# Check for Server Availability
@app.get("/health")
async def health():
    return {"status": "ok"}

# Segment an image
@app.post("/segment")
async def segment(image: np.ndarray | list[np.ndarray], model_settings: dict, cp_settings: dict, target_path: str)-> dict:
    """Expects a JSON payload with the following fields:
    - image: Base64 encoded image data
    - model_settings: Model settings to define the model
    - cp_settings: Cellpose settings, to run the segmentation
    - target_path: Path where the processed image should be saved"""
    pass