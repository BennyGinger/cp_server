from unittest.mock import MagicMock

import pytest

from cp_server.fastapi_app.watcher.event_handlers import TrackFileHandler


class FakeEvent:
    """A simple fake event to simulate the FileCreatedEvent from watchdog"""
    def __init__(self, src_path):
        self.src_path = src_path

@pytest.fixture
def handler(fake_celery):
    """Create a TrackFileHandler with a dummy celery app and a sample stitch_threshold."""
    stitch_threshold = 0.5
    return TrackFileHandler(fake_celery, stitch_threshold)

def test_invalid_filename(handler, fake_celery):
    """Test that an invalid filename does not trigger the task."""
    event = FakeEvent("invalid_file_name.tif")
    handler.on_created(event)
    assert len(fake_celery.tasks) == 0

def test_one_valid_file(handler, fake_celery):
    """
    Test that after processing one valid mask file (time_id "1"),
    the task is not triggered and the file is stored.
    """
    event = FakeEvent("A1_P100_extra_1.tif")
    handler.on_created(event)
    # No task should be submitted yet.
    assert len(fake_celery.tasks) == 0
    
    # Verify that the file is stored under the correct fov and time key.
    assert "A1_P100" in handler.mask_files
    assert handler.mask_files["A1_P100"].get("1") == "A1_P100_extra_1.tif"

def test_two_valid_files(handler, fake_celery):
    """
    Test that after processing two valid mask files for the same fov
    (time_ids "1" and "2"), the tracking task is sent,
    and the internal dictionary is cleared.
    """
    event1 = FakeEvent("A1_P100_extra_1.tif")
    event2 = FakeEvent("A1_P100_extra_2.tif")
    
    # Process the first file; no task should be submitted.
    handler.on_created(event1)
    assert len(fake_celery.tasks) == 0
    
    # Process the second file; the task should now be submitted.
    handler.on_created(event2)
    assert len(fake_celery.tasks) == 1

    task_name, kwargs = fake_celery.tasks[0]
    assert task_name == 'cp_server.tasks_server.celery_tasks.track_cells'
    assert kwargs == {
        "img_files": ["A1_P100_extra_1.tif", "A1_P100_extra_2.tif"],
        "stitch_threshold": handler.stitch_threshold,
    }
    
    # Verify that the mask list for the fov has been cleared.
    assert handler.mask_files["A1_P100"] == {}

def test_two_valid_files_reversed(handler, fake_celery):
    """
    Test that even if the file for time "2" is detected before the file for time "1",
    the task receives the files in the correct order (time "1" first, then time "2").
    """
    event1 = FakeEvent("A1_P100_extra_2.tif")
    event2 = FakeEvent("A1_P100_extra_1.tif")
    
    handler.on_created(event1)
    assert len(fake_celery.tasks) == 0
    
    handler.on_created(event2)
    assert len(fake_celery.tasks) == 1

    task_name, kwargs = fake_celery.tasks[0]
    assert task_name == 'cp_server.tasks_server.celery_tasks.track_cells'
    assert kwargs == {
        "img_files": ["A1_P100_extra_1.tif", "A1_P100_extra_2.tif"],
        "stitch_threshold": handler.stitch_threshold,
    }
    assert handler.mask_files["A1_P100"] == {}

def test_two_single_valid_files(handler, fake_celery):
    """
    Test that if two valid mask files are detected for different fovs, the tasks should not be triggered.
    """
    event1 = FakeEvent("A1_P100_extra_1.tif")
    event2 = FakeEvent("A2_P100_extra_2.tif")
    
    handler.on_created(event1)
    assert len(fake_celery.tasks) == 0
    
    handler.on_created(event2)
    assert len(fake_celery.tasks) == 0
    
    assert "A1_P100" in handler.mask_files
    assert handler.mask_files["A1_P100"].get("1") == "A1_P100_extra_1.tif"
    assert "A2_P100" in handler.mask_files
    assert handler.mask_files["A2_P100"].get("2") == "A2_P100_extra_2.tif"