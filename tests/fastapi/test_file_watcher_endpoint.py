from cp_server.fastapi_app.main import app
from fastapi.testclient import TestClient


# A fake file watcher manager for testing
class FakeFileWatcherManager:
    async def start_watcher(self, **kwargs):
        # Simulate successful start of watcher
        return

    async def stop_watcher(self, directory: str):
        # Simulate successful stop of watcher
        return
    
# Override the manager for tests
app.state.watcher_manager = FakeFileWatcherManager()

client = TestClient(app)

def test_setup_file_watcher(payload):
    # Update the payload with the directory
    payload["directory"] = "test_directory"
    
    # Send a POST request to the endpoint
    response = client.post("/setup-file-watcher", json=payload)
    
    # Check the response status and message
    assert response.status_code == 200
    expected_message = {"message": f"File watcher setup for directory: {payload['directory']}"}
    assert response.json() == expected_message
    
def test_stop_file_watcher():
    directory = "test_directory"
    # You can pass query parameters using the `params` argument or directly include them in the URL
    response = client.post(f"/stop-file-watcher?directory={directory}")
    
    # Check that the endpoint returns a 200 and the expected JSON message
    assert response.status_code == 200
    expected_message = {"message": f"File watcher stopped for directory: {directory}"}
    assert response.json() == expected_message
