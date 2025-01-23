# Default cellpose settings
import json
from fastapi import Query
import numpy as np

CP_SETTINGS = {"batch_size": 8, 
               "channels": [0,0], 
               "channel_axis": None,
               "z_axis": None,
               "normalize": True, 
               "rescale": None, 
               "diameter": 60., 
               "tile_overlap": 0.1,
               "augment": False, 
               "resample": True, 
               "invert": False, 
               "flow_threshold": 0.4,
               "cellprob_threshold": 0.0, 
               "do_3D": False, 
               "anisotropy": None, 
               "stitch_threshold": 0.0,
               "min_size": 15, 
               "niter": None, 
               "interp": True, 
               "bsize": 224, 
               "dP_smooth": 0}

def unpack_settings(cp_settings: str = Query(...),)-> dict:
    # Initialize settings
    cp_eval = CP_SETTINGS.copy()
    
    # Parse settings
    cp_settings = json.loads(cp_settings)
    
    # Update model settings
    for k, v in cp_settings.items():
        if k in CP_SETTINGS:
            cp_eval[k] = v
    return cp_eval

def decode_image(img_bytes: bytes, img_shape: str = Query(...))-> np.ndarray:
    shape = tuple(json.loads(img_shape))
    
    # Convert bytes to numpy array
    img_arr = np.frombuffer(img_bytes, dtype=np.uint16).reshape(shape)
    # # TODO: Check if the image is in the correct format
    # img_arr = np.frombuffer(img_bytes, dtype=np.uint8)
    # img_arr = cv2.imdecode(img_arr, cv2.IMREAD_UNCHANGED)
    # print(f"Image shape2: {img_arr.shape}")
    
    # Convert bytes to a PIL Image
    # img = Image.open(io.BytesIO(img_bytes))
    
    # # Convert PIL Image to numpy array
    # img_arr = np.array(img)
    return img_arr