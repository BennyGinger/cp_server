# Fixture to capture calls to save_masks_task.delay
import pytest
np = pytest.importorskip("numpy")
pytest.importorskip("celery")

from cp_server.tasks_server.tasks.celery_main_task import track_cells


@pytest.fixture
def dummy_save_calls():
    calls = []
    return calls

# Patch external dependencies before each test
@pytest.fixture(autouse=True)
def patch_dependencies(monkeypatch, dummy_save_calls):
    import cp_server.tasks_server.tasks.celery_main_task as celery_main_task
    
    class DummyTiff:
        """Dummy replacement for tiff.imread that returns a predictable 2x2 mask"""
        @staticmethod
        def imread(file):
            # Return different dummy arrays based on the file name
            if file == "img1.tif":
                return np.array([[1, 2], [3, 4]])
            elif file == "img2.tif":
                return np.array([[5, 6], [7, 8]])
            return np.zeros((2, 2), dtype=np.uint16)
    
    # Dummy replacement for track_masks that simulates cell tracking
    def dummy_track_masks(masks, stitch_threshold):
        # For testing, simply add 10 to all mask values to simulate processing.
        return masks + 10
    
    # Patch tiff.imread to use our dummy function
    monkeypatch.setattr(celery_main_task.tiff, "imread", DummyTiff.imread)
    
    # Patch track_masks to use our dummy implementation
    monkeypatch.setattr(celery_main_task, "track_masks", dummy_track_masks)
    
    # Patch save_masks_task.delay to record its calls instead of performing async work.
    monkeypatch.setattr(celery_main_task.save_masks_task, "delay", lambda mask, file: dummy_save_calls.append((mask, file)))

def test_track_cells_returns_message():
    img_files = ["img1.tif", "img2.tif"]
    stitch_threshold = 0.5
    # Call the task function
    result = track_cells(img_files, stitch_threshold)
    # The function should return a message based on the first image filename.
    expected_message = f"Images starting with {img_files[0]} were sent to be tracked"
    assert result == expected_message

def test_track_cells_save_calls(dummy_save_calls):
    img_files = ["img1.tif", "img2.tif"]
    stitch_threshold = 0.5
    # Run the task
    track_cells(img_files, stitch_threshold)
    
    # Verify that save_masks_task.delay was called for each image.
    assert len(dummy_save_calls) == len(img_files)
    
    # Our dummy_imread returns specific arrays; dummy_track_masks adds 10.
    expected_mask_1 = np.array([[1, 2], [3, 4]]) + 10  # for "img1.tif"
    expected_mask_2 = np.array([[5, 6], [7, 8]]) + 10  # for "img2.tif"
    
    # Check first call
    np.testing.assert_array_equal(dummy_save_calls[0][0], expected_mask_1)
    assert dummy_save_calls[0][1] == "img1.tif"
    
    # Check second call
    np.testing.assert_array_equal(dummy_save_calls[1][0], expected_mask_2)
    assert dummy_save_calls[1][1] == "img2.tif"