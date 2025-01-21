from dataclasses import dataclass, field
import logging
from cellpose.denoise import CellposeDenoiseModel
import numpy as np


# Default cellpose settings
MODEL_SETTINGS = {'gpu':True,
                  'model_type': 'cyto2',
                  'pretrained_model':False}


@dataclass
class CellposeModel():
    """Encapsulates the Cellpose model and provides methods to run segmentation"""
    
    model: CellposeDenoiseModel = field(init=False)
    
    def __post_init__(self)-> None:
        # Initialize model
        self.init_model(MODEL_SETTINGS)
    
    def unpack_settings(self, model_settings: dict)-> dict:
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
    
    def init_model(self, model_settings: dict)-> None:
        model_settings = self.unpack_settings(model_settings)
        
        self.model = CellposeDenoiseModel(**model_settings)
    
    def segment(self, image: np.ndarray, cp_settings: dict)-> list[np.ndarray]:
        # Denoise image has a bug and it requires channels list (even if default is set to None by default)
        if "channels" not in cp_settings:
            cp_settings['channels'] = [0, 0]
        
        elif cp_settings['channels'] is None:
            cp_settings['channels'] = [0, 0]
        
        # Run segmentation
        mask: list[np.ndarray] = self.model.eval(image, **cp_settings)[0]
        logging.info(f"Image segmented successfully: {len(mask)} masks created")
        
        return mask