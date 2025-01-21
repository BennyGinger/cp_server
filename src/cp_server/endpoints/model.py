import logging
from fastapi import APIRouter, HTTPException, Request
from cellpose.denoise import CellposeDenoiseModel
from cp_server.utils.model_utils import unpack_settings


router = APIRouter()

@router.post("/model")
async def create_cp_model(request: Request, settings: dict)-> dict:
    """Expects a JSON payload with the following fields:
    - settings: Model settings to define the cellpose model"""
    
    try:
        # Sort out settings
        model_settings = unpack_settings(settings)
        
        # Create a model instance
        cp_model = CellposeDenoiseModel(**model_settings)
        
        # Save it to the app state
        request.app.state.cp_model = cp_model
        
        # Log model update
        logging.info(f"Model {cp_model} was created successfully with settings: {model_settings}")
        
        return {"status": "Model created successfully"}
    except TimeoutError as t:
        logging.error(f"Failed to download the model {t}")
        raise HTTPException(status_code=504, detail=f"Model download failed: {t}")
    except Exception as e:
        logging.error(f"Failed to create model: {e}")
        raise HTTPException(status_code=500, detail=f"Model creation failed: {e}")

