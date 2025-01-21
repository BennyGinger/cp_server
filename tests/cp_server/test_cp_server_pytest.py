import json
import os
from fastapi.testclient import TestClient
import numpy as np
from cp_server.cp_server import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_model():
    payload = {
        "gpu": True,
        "model_type": "cyto3",
        "pretrained_model": False
    }
    response = client.post("/model", json=payload)
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
    
def test_segment():
    # Load the model
    payload = {
        "gpu": True,
        "model_type": "cyto3",
        "pretrained_model": False
    }
    response = client.post("/model", json=payload)
    
    # Create a mock image byte array
    img_arr = np.random.randint(0, 256, (256, 256), dtype=np.uint8)
    img_bytes = img_arr.tobytes()
    img_shape = img_arr.shape
    
    # File input
    files = {"img_file": ("test_image.png", img_bytes, "image/png")}
    
    # Data input
    data = {"settings": json.dumps({'diameter':60.,
                         'flow_threshold':0.4,
                         'cellprob_threshold':0.,}),
            "target_path": "path/to/save",
            "img_shape": json.dumps(img_shape)}
    
    response = client.post("/segment", files=files, params=data)
    
    print(response.json())
    
    assert response.status_code == 200
    assert "mask" in response.json()
    assert response.json()["target_path"] == "path/to/save"

