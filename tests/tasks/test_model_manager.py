import types
import sys
import pytest

from cp_server.tasks_server.tasks.segementation import model_manager as mm


class DummyModel:
    def __init__(self, name):
        self.name = name


@pytest.fixture(autouse=True)
def mock_cellpose_kit(monkeypatch):
    """Mock cellpose-kit setup and eval param functions"""
    # Mock setup_cellpose to return a dict with 'model' and 'lock'
    def fake_setup_cellpose(cellpose_settings, threading, use_nuclear_channel, do_denoise):
        key = f"{cellpose_settings.get('pretrained_model','cyto3')}_{use_nuclear_channel}_{do_denoise}"
        return {'model': DummyModel(key), 'lock': None}

    # Fake eval param configurators
    def fake_v3_eval(current_settings, use_nuc, do_denoise):
        return {'params': ('v3', current_settings.get('diameter', None), use_nuc, do_denoise)}

    def fake_v4_eval(current_settings, use_nuc, do_denoise):
        return {'params': ('v4', current_settings.get('diameter', None), use_nuc, do_denoise)}

    # Fake get_cellpose_version toggled via env key
    def fake_get_version():
        return 'v3'

    fake_api = types.SimpleNamespace(setup_cellpose=fake_setup_cellpose)
    fake_backend_v3 = types.SimpleNamespace(configure_eval_params=fake_v3_eval)
    fake_backend_v4 = types.SimpleNamespace(configure_eval_params=fake_v4_eval)

    # Inject fake modules into sys.modules via monkeypatch
    monkeypatch.setitem(sys.modules, 'cellpose_kit.api', fake_api)
    monkeypatch.setitem(sys.modules, 'cellpose_kit.backend.v3', fake_backend_v3)
    monkeypatch.setitem(sys.modules, 'cellpose_kit.backend.v4', fake_backend_v4)
    # set compat.get_cellpose_version
    compat_mod = types.SimpleNamespace(get_cellpose_version=fake_get_version)
    monkeypatch.setitem(sys.modules, 'cellpose_kit.compat', compat_mod)

    yield


def test_cache_reuse_and_eval_params():
    mgr = mm.ModelManager()
    mgr.clear_cache()

    s1 = {'pretrained_model': 'A', 'use_nuclear_channel': True, 'do_denoise': False, 'diameter': 10}
    cfg1 = mgr.get_configured_settings(s1)

    # Request same model settings but different eval param (diameter) -> should reuse model
    s2 = {'pretrained_model': 'A', 'use_nuclear_channel': True, 'do_denoise': False, 'diameter': 20}
    cfg2 = mgr.get_configured_settings(s2)

    assert cfg1['model'].name == cfg2['model'].name
    assert cfg1['eval_params'] != cfg2['eval_params']

    # Different model settings -> new model
    s3 = {'pretrained_model': 'B', 'use_nuclear_channel': True, 'do_denoise': False}
    cfg3 = mgr.get_configured_settings(s3)
    assert cfg3['model'].name != cfg1['model'].name

    mgr.clear_cache()

    # After clearing, requesting same as s1 will create a new model object
    cfg4 = mgr.get_configured_settings(s1)
    assert cfg4['model'].name == cfg1['model'].name
    # Object identity should differ because cache was cleared
    assert cfg4['model'] is not cfg1['model']


def test_invalid_settings_type():
    mgr = mm.ModelManager()
    with pytest.raises(TypeError):
        mgr.get_configured_settings(None)
