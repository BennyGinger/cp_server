from cellpose.models import CellposeModel
from cellpose.denoise import CellposeDenoiseModel
import numpy as np
import pytest

from cp_server.tasks_server.tasks.segementation.cp_seg import _initialize_cellpose_model, unpack_settings, _segment_image


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

########### Test unpack_settings ############
@pytest.mark.parametrize("do_denoise", [True, False])
def test_unpack_settings(settings, do_denoise):
    
    model_settings, cp_settings = unpack_settings(settings, do_denoise)
    
    assert model_settings == settings["model"]
    match do_denoise:
        case True:
            assert cp_settings["channels"] == [0, 0]
            assert "restore_type" in model_settings
        case False:
            assert cp_settings["channels"] is None
            assert "restore_type" not in model_settings
    assert cp_settings == settings["segmentation"]

def test_unpack_settings_with_missing_channels(settings):
    
    settings["segmentation"].pop("channels")
    
    model_settings, cp_settings = unpack_settings(settings, do_denoise=True)
    
    assert model_settings == settings["model"]
    assert cp_settings["channels"] == [0, 0]
    assert cp_settings == settings["segmentation"]

@pytest.mark.parametrize("model", ["cyto2", "cyto3", "nuclei"])
def test_unpack_settings_with_no_restore_model(settings, model):
    
    settings["model"]['model_type'] = model
    settings["model"].pop("restore_type")
    
    model_settings, _ = unpack_settings(settings, do_denoise=True)
    
    assert "restore_type" in model_settings
    if "cyto" in model:
        assert model_settings['model_type'] in model_settings['restore_type']
    else:
        assert "cyto2" in model_settings['restore_type']
    

########### Test initialize_cellpose_model ############
@pytest.mark.parametrize("do_denoise", [True, False])
def test_initialize_cellpose_model_with_denoise(settings, do_denoise):
    
    model_settings = unpack_settings(settings, do_denoise)[0]
    
    model = _initialize_cellpose_model(do_denoise, model_settings)
    
    match do_denoise:
        case True:
            assert isinstance(model, CellposeDenoiseModel)
            assert model.cp.gpu
        case False:
            assert isinstance(model, CellposeModel)
            assert model.gpu

########### Test segment_image ############
@pytest.mark.parametrize("do_denoise", [True, False])
def test_segment_2Dimage(img, settings, do_denoise):
    
    model_settings, cp_settings = unpack_settings(settings, do_denoise)
    cp_settings['z_axis'] = None
    cp_settings['stitch_threshold'] = 0
    
    model = _initialize_cellpose_model(do_denoise, model_settings)
    
    masks = _segment_image(img, cp_settings, model)
    
    assert masks.shape == img.shape

@pytest.mark.parametrize("threeD_settings", [{"do_3D": False, "stitch_threshold": 0.75}, {"do_3D": True, "stitch_threshold": 0.0}])
def test_segment_3Dimage(img_zstack, settings, threeD_settings):
    do_denoise = True
    
    model_settings, cp_settings = unpack_settings(settings, do_denoise=do_denoise)
    cp_settings.update(threeD_settings)
    
    model = _initialize_cellpose_model(do_denoise=do_denoise, model_settings=model_settings)
    
    masks = _segment_image(img_zstack, cp_settings, model)
    
    assert masks.shape == img_zstack.shape