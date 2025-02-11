from pathlib import Path
import pytest

from cp_server.fastapi_app.main import app
from fastapi.testclient import TestClient


# Set up the TestClient
client = TestClient(app)


# Fixture to override the watcher manager and create a temporary directory with dummy files
@pytest.fixture
def setup_fake_env(tmp_path, fake_manager):
    # Create a subfolder that will act as the src_folder
    src_folder = tmp_path.joinpath("source_folder")
    src_folder.mkdir()
    
    # Create dummy .tif files inside the src_folder
    src_folder.joinpath("image_test_1.tif").write_text("dummy image content")
    src_folder.joinpath("image2_test_.tif").write_text("dummy image content")
    
    # Optionally, create a file that should be ignored (e.g., wrong extension or in the wrong folder)
    tmp_path.joinpath("not_in_src.txt").write_text("ignored file")
    
    # Create and set the fake watcher manager
    app.state.watcher_manager = fake_manager
    
    # Return both the temporary directory (as a Path) and the fake manager for assertions
    return tmp_path, fake_manager

def test_segment_endpoint(setup_fake_env, payload):
    tmp_dir, fake_manager = setup_fake_env

    # Prepare a payload matching your PayLoad model.
    # Note that the endpoint expects an additional field 'src_folder'
    payload["directory"] = str(tmp_dir)
    payload["src_folder"] = "source_folder"
    
    # Send the POST request with the JSON payload.
    response = client.post("/segment", json=payload)
    
    # Check the response: the endpoint should return a message with the directory and settings.
    expected_message = f"Processing images in {payload['directory']} with settings: {payload['settings']}"
    assert response.status_code == 200
    assert response.json() == {"message": expected_message}
    
    # Verify that celery_app.send_task was called for each qualifying .tif file.
    dummy_celery = fake_manager.celery_app
    assert len(dummy_celery.tasks) == 2

    # Check if the task was called with the expected arguments.
    for task_name, kwargs in dummy_celery.tasks:
        assert task_name == "cp_server.task_server.celery_task.process_images"
        # Check the passed args:
        assert kwargs["settings"] == payload["settings"]
        assert kwargs["dst_folder"] == payload["dst_folder"]
        assert kwargs["key_label"] == payload["key_label"]
        assert kwargs["do_denoise"] == payload["do_denoise"]
        # And that 'img_file' is a Path object pointing to a .tif file:
        assert isinstance(kwargs["img_file"], Path)
        assert kwargs["img_file"].suffix == ".tif"