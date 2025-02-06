from pathlib import Path
import numpy as np
import tifffile as tiff

from cp_server.task_server.tasks.saving.save_arrays import save_mask, save_img


############ Test save_mask ############
<<<<<<< HEAD
def test_save_mask_refseg(create_file, img):
    # Create fake file
    img_file: Path = create_file("test_refseg_1.tif")
=======
def test_save_mask_refseg(temp_dir, img):
    # Create fake file
    img_file: Path = temp_dir("test_refseg_1.tif")
>>>>>>> 2d8dea9d55aa1116b3e8cbc65312ce3778c5efa2
    
    dst_folder = "output"
    key_label = "refseg"
    
    # Call the function
    save_mask(img, img_file, dst_folder, key_label)
    
    # Expected path
    expected_dir = img_file.parent.parent.joinpath(dst_folder)
    expected_file = expected_dir.joinpath("test_mask_1.tif")
    
    assert expected_dir.exists(), "The destination directory was not created."
    assert expected_file.exists(), f"The file {expected_file} was not created."

    saved_mask = tiff.imread(str(expected_file))
    np.testing.assert_array_equal(img.astype("uint16"), saved_mask)

<<<<<<< HEAD
def test_save_mask_z(create_file, img):
    # Create fake file
    img_file: Path = create_file("test_z_1.tif")
=======
def test_save_mask_z(temp_dir, img):
    # Create fake file
    img_file: Path = temp_dir("test_z_1.tif")
>>>>>>> 2d8dea9d55aa1116b3e8cbc65312ce3778c5efa2
    
    dst_folder = "output"
    key_label = "_z"
    
    # Call the function
    save_mask(img, img_file, dst_folder, key_label)
    
    # Expected path
    expected_dir = img_file.parent.parent.joinpath(dst_folder)
    expected_file = expected_dir.joinpath("test_z_1.tif")
    
    assert expected_dir.exists(), "The destination directory was not created."
    assert expected_file.exists(), f"The file {expected_file} was not created."
    
    saved_mask = tiff.imread(str(expected_file))
    np.testing.assert_array_equal(img.astype("uint16"), saved_mask)

########### Test save_img ############
def test_save_img(img, temp_dir):
    # Create fake file
    img_file = temp_dir.joinpath("test_img.tif")
    
    # Call the function
    save_img(img, img_file)
    
    assert img_file.exists(), f"The file {img_file} was not created."
    
    saved_img = tiff.imread(str(img_file))
    np.testing.assert_array_equal(img.astype("uint16"), saved_img)