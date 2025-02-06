from cellpose.models import CellposeModel
from cellpose.denoise import CellposeDenoiseModel
import numpy as np
import pytest

from cp_server.task_server.tasks.segementation.cp_seg import initialize_cellpose_model, unpack_settings, segment_image


@pytest.fixture
def settings():
    return {
        "model": {
            "model_type": "cyto2",
            "restore_type": "denoise_cyto2",
            "gpu": True,},
        
        "segmentation": {
            "channels": None,
            "diameter": 60,
            "flow_threshold": 0.4,
            "cellprob_threshold": 0.0,
            "z_axis": 0,
            "do_3D": False,
            "stitch_threshold": 0.75,}}

@pytest.fixture
def img():
    return np.random.randint(0, 65536, (256, 256), dtype=np.uint16)

@pytest.fixture
def img_zstack():
    return np.random.randint(0, 65536, (10, 256, 256), dtype=np.uint16)

########### Test unpack_settings ############
def test_unpack_settings_with_denoise(settings):
    
    model_settings, cp_settings = unpack_settings(settings, do_denoise=True)
    
    assert model_settings == settings["model"]
    assert cp_settings["channels"] == [0, 0]
    assert cp_settings == settings["segmentation"]

def test_unpack_settings_without_denoise(settings):
    
    model_settings, cp_settings = unpack_settings(settings, do_denoise=False)
    
    assert "restore_type" not in model_settings
    assert model_settings == settings["model"]
    assert cp_settings["channels"] is None
    assert cp_settings == settings["segmentation"]

def test_unpack_settings_with_missing_channels(settings):
    
    settings["segmentation"].pop("channels")
    
    model_settings, cp_settings = unpack_settings(settings, do_denoise=True)
    
    assert model_settings == settings["model"]
    assert cp_settings["channels"] == [0, 0]
    assert cp_settings == settings["segmentation"]

########### Test initialize_cellpose_model ############
def test_initialize_cellpose_model_with_denoise(settings):
    do_denoise = True
    
    model_settings = unpack_settings(settings, do_denoise=do_denoise)[0]
    
    model = initialize_cellpose_model(do_denoise=do_denoise, model_settings=model_settings)
    
    assert isinstance(model, CellposeDenoiseModel)
    assert model.cp.gpu

def test_initialize_cellpose_model_without_denoise(settings):
    do_denoise = False
    
    model_settings = unpack_settings(settings, do_denoise=do_denoise)[0]
    
    model = initialize_cellpose_model(do_denoise=do_denoise, model_settings=model_settings)
    
    assert isinstance(model, CellposeModel)
    assert model.gpu

########### Test segment_image ############
def test_segment_2Dimage_with_denoise(img, settings):
    do_denoise = True
    
    model_settings, cp_settings = unpack_settings(settings, do_denoise=do_denoise)
    cp_settings['z_axis'] = None
    cp_settings['stitch_threshold'] = 0
    
    model = initialize_cellpose_model(do_denoise=do_denoise, model_settings=model_settings)
    
    masks = segment_image(img, cp_settings, model)
    
    assert masks.shape == img.shape

def test_segment_2Dimage_without_denoise(img, settings):
    do_denoise = False
    
    model_settings, cp_settings = unpack_settings(settings, do_denoise=do_denoise)
    cp_settings['z_axis'] = None
    cp_settings['stitch_threshold'] = 0
    
    model = initialize_cellpose_model(do_denoise=do_denoise, model_settings=model_settings)
    
    masks = segment_image(img, cp_settings, model)
    
    assert masks.shape == img.shape

def test_segment_3Dimage_with_denoise(img_zstack, settings):
    do_denoise = True
    
    model_settings, cp_settings = unpack_settings(settings, do_denoise=do_denoise)
    
    model = initialize_cellpose_model(do_denoise=do_denoise, model_settings=model_settings)
    
    masks = segment_image(img_zstack, cp_settings, model)
    
    assert masks.shape == img_zstack.shape