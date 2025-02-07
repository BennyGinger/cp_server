from pathlib import Path
import numpy as np
import pytest
import tifffile as tiff

from cp_server.task_server.tasks.saving.save_arrays import save_mask, save_img


############ Test save_mask ############
@pytest.mark.parametrize("key_label", ["refseg", "_z"])
def test_save_mask_refseg(temp_dir, img, key_label):
    # Create fake file
    img_file: Path = temp_dir.joinpath(f"test_{key_label}_1.tif".replace("__", "_"))
    
    dst_folder = "output"
    
    # Call the function
    save_mask(img, img_file, dst_folder, key_label)
    
    # Expected path
    expected_dir = img_file.parent.parent.joinpath(dst_folder)
    match key_label:
        case "refseg":
            expected_file = expected_dir.joinpath("test_mask_1.tif")
        case "_z":
            expected_file = expected_dir.joinpath("test_z_1.tif")
    
    assert expected_dir.exists(), "The destination directory was not created."
    assert expected_file.exists(), f"The file {expected_file} was not created."

    saved_mask = tiff.imread(str(expected_file))
    np.testing.assert_array_equal(img.astype("uint16"), saved_mask)

########### Test save_img ############
def test_save_img(temp_dir, img):
    # Create fake file
    img_file = temp_dir.joinpath("test_img.tif")
    
    # Call the function
    save_img(img, img_file)
    
    assert img_file.exists(), f"The file {img_file} was not created."
    
    saved_img = tiff.imread(str(img_file))
    np.testing.assert_array_equal(img.astype("uint16"), saved_img)