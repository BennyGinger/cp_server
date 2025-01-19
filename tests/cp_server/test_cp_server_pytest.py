from fastapi.testclient import TestClient
from cp_server.cp_server_fastapi import app

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
    response = client.post("/model/", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "Model created successfully"}
    
    
    
# def test_segment():
#     # Example payload
#     payload = {
#         "img_lst": [[1, 2], [3, 4]],
#         "settings": {"some_setting": "value"},
#         "target_path": "path/to/save"
#     }
#     response = client.post("/segment/", json=payload)
#     assert response.status_code == 200
#     assert "status" in response.json()