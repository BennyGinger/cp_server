import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

# Import the endpoints router and the payload models.
from cp_server.fastapi_app.endpoints.file_watcher import router as file_watcher
from cp_server.fastapi_app.watcher.event_handlers import SegmentFileHandler, TrackFileHandler

@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(file_watcher)
    # Create dummy instances for the watcher_manager and celery_app.
    dummy_watcher_manager = MagicMock()
    dummy_celery_app = MagicMock()
    # Attach them to the application state.
    app.state.watcher_manager = dummy_watcher_manager
    app.state.celery_app = dummy_celery_app
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_start_segment_watcher(client, payload):
    # Define a payload with all required fields.
    payload['directory'] = "/tmp/watch"
    
    response = client.post("/start-segment-watcher", json=payload)
    assert response.status_code == 200
    expected_message = f"File watcher setup for segmenting images in directory: {payload['directory']}"
    assert response.json() == {"message": expected_message}
    
    # Verify that the watcher_manager's start_watcher method was called.
    watcher_manager = client.app.state.watcher_manager
    watcher_manager.start_watcher.assert_called_once()
    
    # Inspect the arguments passed to start_watcher.
    _, call_kwargs = watcher_manager.start_watcher.call_args
    assert call_kwargs.get("directory") == payload["directory"]
    
    event_handler = call_kwargs.get("event_handler")
    # Check that the event_handler is an instance of SegmentFileHandler.
    assert isinstance(event_handler, SegmentFileHandler)
    
    # Verify that the event_handler was created with the dummy celery_app and correct parameters.
    dummy_celery_app = client.app.state.celery_app
    assert event_handler.celery_app == dummy_celery_app
    assert event_handler.settings == payload["settings"]
    assert event_handler.dst_folder == payload["dst_folder"]
    assert event_handler.key_label == payload["key_label"]
    assert event_handler.do_denoise == payload["do_denoise"]

def test_start_tracking_watcher(client, track_payload):
    response = client.post("/start-tracking-watcher", json=track_payload)
    assert response.status_code == 200
    expected_message = f"File watcher setup for tracking masks in directory: {track_payload["directory"]}"
    assert response.json() == {"message": expected_message}
    
    # Verify that the watcher_manager's start_watcher method was called.
    watcher_manager = client.app.state.watcher_manager
    watcher_manager.start_watcher.assert_called_once()
    
    # Inspect the arguments passed to start_watcher.
    _, call_kwargs = watcher_manager.start_watcher.call_args
    assert call_kwargs.get("directory") == track_payload["directory"]
    
    event_handler = call_kwargs.get("event_handler")
    # Check that the event_handler is an instance of SegmentFileHandler.
    assert isinstance(event_handler, TrackFileHandler)
    
    # Verify that the event_handler was created with the dummy celery_app and correct parameters.
    dummy_celery_app = client.app.state.celery_app
    assert event_handler.celery_app == dummy_celery_app
    assert event_handler.stitch_threshold == track_payload["stitch_threshold"]


def test_stop_directory_watcher(client):
    payload = {"directory": "/tmp/watch"}
    response = client.post("/stop-dir-watcher", json=payload)
    assert response.status_code == 200
    expected_message = f"File watcher stopped for directory: {payload['directory']}"
    assert response.json() == {"message": expected_message}
    
    # Verify that the watcher_manager's stop_watcher was called with the correct directory.
    watcher_manager = client.app.state.watcher_manager
    watcher_manager.stop_watcher.assert_called_once_with(directory=payload["directory"])
