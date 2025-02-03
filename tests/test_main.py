from fastapi.testclient import TestClient
from cp_server.main import app
from cp_server.brocker_service.redis_server import is_redis_running
from cp_server.celery_server.celery_server import is_celery_running

# Create a test client for FastAPI
client = TestClient(app)

def test_read_root():
    """Test if the FastAPI server is running."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "FastAPI server is running with Celery and Redis"}

def test_redis_running():
    """Check if Redis server is running."""
    assert is_redis_running(), "Redis is not running!"

def test_celery_running():
    """Check if Celery worker is running."""
    assert is_celery_running(), "Celery is not running!"

def test_stop_services():
    """Test stopping Redis and Celery services."""
    response = client.post("/stop")
    assert response.status_code == 200
    assert response.json() == {"message": "Stopped Celery and Redis services"}

    # Check if Redis and Celery are stopped
    assert not is_redis_running(), "Redis is still running!"
    assert not is_celery_running(), "Celery is still running!"