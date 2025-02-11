from cp_server.fastapi_app.main import app
from fastapi.testclient import TestClient


client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"message": "FastAPI server is running, and file watcher is initiated."}