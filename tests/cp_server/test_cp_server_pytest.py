import json
import os
import pytest
from fastapi.testclient import TestClient
import numpy as np
from cp_server.cp_server import app


client = TestClient(app)

@pytest.fixture
def model_settings():
    return {"gpu": True,
            "model_type": "cyto3",
            "pretrained_model": False}

@pytest.fixture
def img():
    img_arr = np.random.randint(0, 65536, (256, 256), dtype=np.uint16)
    img_bytes = img_arr.tobytes()
    img_shape = img_arr.shape
    return img_bytes, img_shape

@pytest.fixture
def cp_settings():
    return {"settings": json.dumps({'diameter':60.,
                         'flow_threshold':0.4,
                         'cellprob_threshold':0.,}),
            "target_path": "path/to/save",}

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_model(model_settings):
    response = client.post("/model", json=model_settings)
    assert response.status_code == 200
    assert response.json() == {"status": "Model created successfully"}
    
def test_shutdown(monkeypatch):
    # Mock function to replace os.kill
    def mock_kill(pid, sig):
        pass  

    monkeypatch.setattr(os, "kill", mock_kill)
    
    response = client.post("/shutdown")
    assert response.status_code == 200
    assert response.json() == {"message": "Server shutting down..."}
    
def test_segment(model_settings, img, cp_settings):
    # Load the model
    response = client.post("/model", json=model_settings)
    
    # Create a mock image byte array
    img_bytes, img_shape = img
    
    # File input
    files = {"img_file": ("test_image.png", img_bytes, "image/png")}
    
    # Data input
    data = cp_settings
    data["img_shape"] = json.dumps(img_shape)
    
    # Test the /segment endpoint
    response = client.post("/segment", files=files, params=data)
    
    print(response.json())
    
    assert response.status_code == 200
    assert "mask" in response.json()
    assert response.json()["target_path"] == "path/to/save"

