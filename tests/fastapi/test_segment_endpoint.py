from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from cp_server.fastapi_app.main import app

# Dummy celery class that records tasks sent to it.
class DummyCelery:
    def __init__(self):
        self.tasks = []  # List to record (task_name, kwargs) tuples.
    def send_task(self, task_name, kwargs):
        self.tasks.append((task_name, kwargs))

# Fake manager that simply holds a celery_app attribute.
class FakeManager:
    def __init__(self, celery_app):
        self.celery_app = celery_app

# Fixture that creates a dummy celery instance.
@pytest.fixture
def dummy_celery():
    return DummyCelery()

# Fixture that creates a fake watcher manager holding the dummy celery.
@pytest.fixture
def fake_manager(dummy_celery):
    return FakeManager(dummy_celery)

# TestClient using the main app.
client = TestClient(app)

# Fixture to create a fake file environment.
@pytest.fixture
def setup_fake_env(tmp_path, fake_manager, dummy_celery):
    # Create a subfolder that will act as the source folder.
    src_folder = tmp_path.joinpath("source_folder")
    src_folder.mkdir()
    
    # Create dummy .tif files inside the src_folder.
    src_folder.joinpath("image_test_1.tif").write_text("dummy image content")
    src_folder.joinpath("image2_test_.tif").write_text("dummy image content")
    
    # Create a file that should be ignored.
    tmp_path.joinpath("not_in_src.txt").write_text("ignored file")
    
    # Set the fake watcher manager and dummy celery on the app state.
    app.state.watcher_manager = fake_manager
    app.state.celery_app = dummy_celery
    
    # Return the temporary directory and the fake manager for further assertions.
    return tmp_path, fake_manager


def test_segment_endpoint(setup_fake_env, payload):
    tmp_dir, fake_manager = setup_fake_env

    # The endpoint expects 'directory' and an additional 'src_folder'.
    payload["directory"] = str(tmp_dir)
    payload["src_folder"] = "source_folder"
    
    # Send the POST request.
    response = client.post("/segment", json=payload)
    
    # Verify the response.
    expected_message = f"Processing images in {payload['directory']} with settings: {payload['settings']}"
    assert response.status_code == 200
    assert response.json() == {"message": expected_message}
    
    # Verify that celery_app.send_task was called for each qualifying .tif file.
    dummy_celery = fake_manager.celery_app
    # We expect 2 tasks since we have 2 .tif files in the proper src_folder.
    assert len(dummy_celery.tasks) == 2

    # Check if the tasks were called with the expected arguments.
    for task_name, kwargs in dummy_celery.tasks:
        assert task_name == "cp_server.tasks_server.celery_tasks.process_images"
        # Verify each argument.
        assert kwargs["settings"] == payload["settings"]
        assert kwargs["dst_folder"] == payload["dst_folder"]
        assert kwargs["key_label"] == payload["key_label"]
        assert kwargs["do_denoise"] == payload["do_denoise"]
        # 'img_file' should be a string path ending in .tif.
        assert isinstance(kwargs["img_file"], str)
        assert Path(kwargs["img_file"]).suffix == ".tif"
