from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest
from tifffile import imread

from cp_server.task_server.celery_task import save_masks_task
from cp_server.task_server.celery_task import segment


@pytest.mark.parametrize("key_label", ["refseg", "_z"])
def test_save_masks_task(temp_dir, img, key_label):
    """Test save_img_task to ensure it saves the image correctly.
    """
    
    # Create a dummy image path and dst_folder
    img_file: Path = temp_dir.joinpath(f"test_{key_label}_1.tif".replace("__", "_"))
    dst_folder = "output"
    
    # Call the real task (no monkeypatch)
    save_masks_task(img, img_file, dst_folder, key_label)
    
    # Expected path
    expected_dir = img_file.parent.parent.joinpath(dst_folder)
    match key_label:
        case "refseg":
            expected_file = expected_dir.joinpath("test_mask_1.tif")
        case "_z":
            expected_file = expected_dir.joinpath("test_z_1.tif")
    
    # Ensure the file was created
    assert expected_dir.exists(), "The destination directory was not created."
    assert expected_file.exists(), f"The file {expected_file} was not created."
    
    # Load the file to check shape
    loaded_img = imread(expected_file)
    assert loaded_img.shape == img.shape
    assert loaded_img.dtype == img.dtype
    
def test_segment(monkeypatch, temp_dir, img):
    """Test segment task to ensure it calls run_seg and then save_masks_task.delay with correct arguments."""

    img_file = temp_dir.joinpath("segmented_cell.tif")
    
    # 1) Mock run_seg so it returns a known array
    def mock_run_seg(settings, img, do_denoise):
        return np.full_like(img, fill_value=42)  # fill with 42
    
    monkeypatch.setattr("cp_server.task_server.celery_task.run_seg", 
                        mock_run_seg)
    
    # 2) Mock save_masks_task.delay to verify it's called with the result
    mock_save_delay = MagicMock()
    monkeypatch.setattr("cp_server.task_server.celery_task.save_masks_task.delay", 
                        mock_save_delay)
    
    # 3) Execute segment
    result = segment({"segmentation":{"abc":[1,2]}, "model":{"def":[3,4]}}, img, img_file, "output", "refseg")
    
    # 4) Verify run_seg was called
    assert (result == 42).all(), "segment should return array of 42"
    
    # 5) Verify save_masks_task.delay was called once with the expected masks
    mock_save_delay.assert_called_once()
    call_args = mock_save_delay.call_args[0]  # (masks, img_file, dst_folder, key_label)
    masks_arg, file_arg, dst_folder_arg, key_label_arg = call_args
    assert (masks_arg == 42).all()
    assert file_arg == img_file
    assert dst_folder_arg == "output"
    assert key_label_arg == "refseg"
    
    