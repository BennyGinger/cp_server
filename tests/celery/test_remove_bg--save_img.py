from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
from tifffile import imread

from cp_server.task_server.celery_task import save_img_task
from cp_server.task_server.celery_task import remove_bg


def test_save_img_task(create_file, img):
    """Test save_img_task to ensure it saves the image correctly.
    """
    
    # Create a dummy image
    out_file: Path = create_file("out_img.tif")

    # Call the real task (no monkeypatch)
    save_img_task(img, out_file)

    # Ensure the file was created
    assert out_file.exists(), f"Expected {out_file} to be created."

    # Load the file to check shape
    loaded_img = imread(out_file)
    assert loaded_img.shape == img.shape
    assert loaded_img.dtype == img.dtype


def test_remove_bg(monkeypatch, temp_dir, img):
    """
    Test remove_bg task to ensure it calls apply_bg_sub 
    and then save_img_task.delay with correct arguments.
    """
    out_file = temp_dir.joinpath("bg_removed.tif")

    # 1) Mock apply_bg_sub so it returns a known array
    def mock_apply_bg_sub(img, **kwargs):
        return np.full_like(img, fill_value=42)  # fill with 42

    monkeypatch.setattr("cp_server.task_server.celery_task.apply_bg_sub",
                        mock_apply_bg_sub)

    # 2) Mock save_img_task.delay to verify it's called with the result
    mock_save_delay = MagicMock()
    monkeypatch.setattr("cp_server.task_server.celery_task.save_img_task.delay",
                        mock_save_delay)

    # 3) Execute remove_bg
    result = remove_bg(img, out_file, some_param="test")

    # 4) Verify apply_bg_sub was called
    assert (result == 42).all(), "remove_bg should return array of 42"
    
    # 5) Verify save_img_task.delay was called once with the expected background image
    mock_save_delay.assert_called_once()
    call_args = mock_save_delay.call_args[0]  # (bg_img, img_file)
    bg_img_arg, file_arg = call_args
    assert (bg_img_arg == 42).all()
    assert file_arg == out_file
