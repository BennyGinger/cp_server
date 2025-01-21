

# Default cellpose settings
MODEL_SETTINGS = {'gpu':True,
                  'model_type': 'cyto2',
                  'pretrained_model':False}

MODEL_TO_FILE_NAMES = {"cyto2": "cyto2torch_0",
                       "cyto": "cytotorch_0",
                       "cyto2_cp3": "cyto2_cp3",
                       "cyto3": "cyto3",
                       "nuclei": "nucleitorch_0",
                       "tissuenet_cp3": "tissuenet_cp3",
                       "livecell_cp3": "livecell_cp3",
                       "yeast_PhC_cp3": "yeast_PhC_cp3",
                       "yeast_BF_cp3": "yeast_BF_cp3",
                       "bact_phase_cp3": "bact_phase_cp3",
                       "bact_fluor_cp3": "bact_fluor_cp3",
                       "deepbacs_cp3": "deepbacs_cp3",
                       "CPx": "CPx"}

RESTORE_MODELS = {"cyto2": "denoise_cyto2", 
                  "cyto3": "denoise_cyto3"}

def unpack_settings(model_settings: dict)-> dict:
    # Update model settings
    for k, v in model_settings.items():
        if k in MODEL_SETTINGS:
            model_settings[k] = v
    
    # Set restore type
    if model_settings['model_type'] in RESTORE_MODELS:
        model_settings['restore_type'] = RESTORE_MODELS[model_settings['model_type']]
    else:
        model_settings['restore_type'] = "denoise_cyto2"
    return model_settings

# def is_model_downloaded(model_settings: dict)-> bool:
#     # If use a custom model
#     if model_settings['model_type'] is None and isinstance(model_settings['pretrained_model'], str):
#         return True
    
#     # Check if the model is downloaded
#     model_path = f"~/.cellpose/models/{MODEL_TO_FILE_NAMES[model_settings['model_type']]}"
#     start_time = time.time()
#     timeout = 600 # 10 minutes
    
#     while not os.path.exists(model_path):
#         if time.time() - start_time >= timeout:
#             raise TimeoutError("Model download timed out")
#         time.sleep(0.5)
#     return True