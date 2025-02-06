from pathlib import Path
import numpy as np
import pytest
import tifffile as tiff

from cp_server.task_server.tasks.saving.save_arrays import save_mask, save_img


@pytest.fixture
def array():
    return np.array([[1, 2], [3, 4]])

@pytest.fixture
def temp_dir(tmp_path)-> Path:
    # Create temp dir structure
    temp_dir = tmp_path.joinpath("level1", "level2")
    temp_dir.mkdir(parents=True)
    return temp_dir

@pytest.fixture
def create_img_file(temp_dir: Path):
    def _create_file(filename: str)-> Path:
        img_file = temp_dir.joinpath(filename)
        img_file.touch()
        return img_file
    return _create_file

############ Test save_mask ############
def test_save_mask_refseg(create_img_file, array):
    # Create fake file
    img_file: Path = create_img_file("test_refseg_1.tif")
    
    dst_folder = "output"
    key_label = "refseg"
    
    # Call the function
    save_mask(array, img_file, dst_folder, key_label)
    
    # Expected path
    expected_dir = img_file.parent.parent.joinpath(dst_folder)
    expected_file = expected_dir.joinpath("test_mask_1.tif")
    
    assert expected_dir.exists(), "The destination directory was not created."
    assert expected_file.exists(), f"The file {expected_file} was not created."

    saved_mask = tiff.imread(str(expected_file))
    np.testing.assert_array_equal(array.astype("uint16"), saved_mask)

def test_save_mask_z(create_img_file, array):
    # Create fake file
    img_file: Path = create_img_file("test_z_1.tif")
    
    dst_folder = "output"
    key_label = "_z"
    
    # Call the function
    save_mask(array, img_file, dst_folder, key_label)
    
    # Expected path
    expected_dir = img_file.parent.parent.joinpath(dst_folder)
    expected_file = expected_dir.joinpath("test_z_1.tif")
    
    assert expected_dir.exists(), "The destination directory was not created."
    assert expected_file.exists(), f"The file {expected_file} was not created."
    
    saved_mask = tiff.imread(str(expected_file))
    np.testing.assert_array_equal(array.astype("uint16"), saved_mask)

########### Test save_img ############
def test_save_img(array, temp_dir):
    # Create fake file
    img_file = temp_dir.joinpath("test_img.tif")
    
    # Call the function
    save_img(array, img_file)
    
    assert img_file.exists(), f"The file {img_file} was not created."
    
    saved_img = tiff.imread(str(img_file))
    np.testing.assert_array_equal(array.astype("uint16"), saved_img)