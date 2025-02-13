from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
from tifffile import imread

from cp_server.tasks_server.celery_tasks import save_img_task
from cp_server.tasks_server.celery_tasks import remove_bg
from cp_server.tasks_server.utils import encode_ndarray_as_bytesb64, decode_bytesb64_to_array


def test_save_img_task(create_file, img):
    """Test save_img_task to ensure it saves the image correctly.
    """
    
    # Create a dummy image
    out_file = str(create_file("out_img.tif"))

    # Call the real task (no monkeypatch)
    img_b64 = encode_ndarray_as_bytesb64(img)
    save_img_task(img_b64, out_file)

    # Ensure the file was created
    assert Path(out_file).exists(), f"Expected {out_file} to be created."

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

    monkeypatch.setattr("cp_server.tasks_server.celery_tasks.apply_bg_sub",
                        mock_apply_bg_sub)

    # 2) Mock save_img_task.delay to verify it's called with the result
    mock_save_delay = MagicMock()
    monkeypatch.setattr("cp_server.tasks_server.celery_tasks.save_img_task.delay",
                        mock_save_delay)

    # 3) Execute remove_bg
    img_b64 = encode_ndarray_as_bytesb64(img)
    result_b64 = remove_bg(img_b64, out_file, some_param="test")

    # 4) Verify apply_bg_sub was called
    result = decode_bytesb64_to_array(result_b64)
    assert (result == 42).all(), "remove_bg should return array of 42"
    
    # 5) Verify save_img_task.delay was called once with the expected background image
    mock_save_delay.assert_called_once()
    call_args = mock_save_delay.call_args[0]  # (bg_img, img_file)
    bg_img_b64_arg, file_arg = call_args
    bg_img_arg = decode_bytesb64_to_array(bg_img_b64_arg)
    assert (bg_img_arg == 42).all()
    assert file_arg == out_file
