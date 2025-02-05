from cellpose.models import CellposeModel
from cellpose.denoise import CellposeDenoiseModel
import numpy as np
import pytest

from cp_server.task_server.tasks.segementation.cp_seg import initialize_cellpose_model, unpack_settings, segment_image


def test_unpack_settings_with_denoise():
    settings = {
        "model": {
            "model_type": "cyto2",
            "restore_type": "denoise_cyto2",
            "gpu": True,
        },
        "segmentation": {
            "channels": None,
            "diameter": 60,
            "flow_threshold": 0.4,
            "cellprob_threshold": 0.0,
            "z_axis": 0,
            "do_3D": False,
            "stitch_threshold": 0.75,
        }
    }
    model_settings, cp_settings = unpack_settings(settings, do_denoise=True)
    assert model_settings == settings["model"]
    assert cp_settings["channels"] == [0, 0]

def test_unpack_settings_without_denoise():
    settings = {
        "model": {
            "model_type": "cyto2",
            "restore_type": "denoise_cyto2",
            "gpu": True,
        },
        "segmentation": {
            "channels": None,
            "diameter": 60,
            "flow_threshold": 0.4,
            "cellprob_threshold": 0.0,
            "z_axis": 0,
            "do_3D": False,
            "stitch_threshold": 0.75,
        }
    }
    model_settings, cp_settings = unpack_settings(settings, do_denoise=False)
    assert "restore_type" not in model_settings
    assert model_settings == {"model_type": "cyto2", "gpu": True}
    assert cp_settings == settings["segmentation"]

def test_unpack_settings_with_missing_channels():
    settings = {
        "model": {
            "model_type": "cyto2",
            "restore_type": "denoise_cyto2",
            "gpu": True,
        },
        "segmentation": {
            "diameter": 60,
            "flow_threshold": 0.4,
            "cellprob_threshold": 0.0,
            "z_axis": 0,
            "do_3D": False,
            "stitch_threshold": 0.75,
        }
    }
    model_settings, cp_settings = unpack_settings(settings, do_denoise=True)
    assert model_settings == settings["model"]
    assert cp_settings["channels"] == [0, 0]


def test_initialize_cellpose_model_with_denoise():
    model_settings = {
        "model_type": "cyto2",
        "restore_type": "denoise_cyto2",
        "gpu": True,
    }
    model = initialize_cellpose_model(do_denoise=True, model_settings=model_settings)
    assert isinstance(model, CellposeDenoiseModel)
    assert model.cp.gpu

def test_initialize_cellpose_model_without_denoise():
    model_settings = {
        "model_type": "cyto2",
        "gpu": True,
    }
    model = initialize_cellpose_model(do_denoise=False, model_settings=model_settings)
    assert isinstance(model, CellposeModel)
    assert model.gpu


@pytest.fixture
def img():
    return np.random.randint(0, 65536, (256, 256), dtype=np.uint16)

@pytest.fixture
def img_zstack():
    return np.random.randint(0, 65536, (10, 256, 256), dtype=np.uint16)
    
def test_segment_image_with_denoise(img):
    cp_settings = {
        "channels": [0, 0],
        "diameter": 60,
        "flow_threshold": 0.4,
        "cellprob_threshold": 0.0,
        "do_3D": False}
    
    model_settings = {
        "model_type": "cyto2",
        "restore_type": "denoise_cyto2",
        "gpu": True,}
    
    model = initialize_cellpose_model(do_denoise=True, model_settings=model_settings)
    masks = segment_image(img, cp_settings, model)
    assert masks.shape == img.shape

def test_segment_image_without_denoise(img):
    cp_settings = {
        "channels": [0, 0],
        "diameter": 60,
        "flow_threshold": 0.4,
        "cellprob_threshold": 0.0,
        "do_3D": False}
    
    model_settings = {
        "model_type": "cyto2",
        "gpu": True,}
    
    model = initialize_cellpose_model(do_denoise=False, model_settings=model_settings)
    masks = segment_image(img, cp_settings, model)
    assert masks.shape == img.shape

def test_segment_image_with_zstack(img_zstack):
    cp_settings = {
        "channels": [0, 0],
        "diameter": 60,
        "flow_threshold": 0.4,
        "cellprob_threshold": 0.0,
        "do_3D": False,
        "z_axis": 0,
        "stitch_threshold": 0.75}
    
    model_settings = {
        "model_type": "cyto2",
        "restore_type": "denoise_cyto2",
        "gpu": True,}
    
    model = initialize_cellpose_model(do_denoise=True, model_settings=model_settings)
    masks = segment_image(img_zstack, cp_settings, model)
    assert masks.shape == img_zstack.shape