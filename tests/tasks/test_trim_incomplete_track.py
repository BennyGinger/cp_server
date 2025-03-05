import numpy as np

from cp_server.tasks_server.tasks.track.track_utils import trim_incomplete_track


def test_trim_incomplete_track_basic():
    """
    Test with a simple 2-frame array.
    Frame 0 has only object 1.
    Frame 1 has objects 1 and 2.
    Expected: object 1 appears in both frames, so only 2 should be removed.
    """
    # Create a 2-frame, 2x2 array
    arr = np.array([
        [[1, 1],
         [1, 1]],
        [[1, 2],
         [2, 1]]
    ])
    # Call the function
    removed_objects = trim_incomplete_track(arr)
    
    # Check that object 2 is identified for removal.
    np.testing.assert_array_equal(np.sort(removed_objects), np.array([2]))
    
    # Verify that all occurrences of 2 are now 0.
    assert not np.any(arr == 2)
    
    # Verify that frame 0 remains unchanged and frame 1 has 2 replaced with 0.
    expected_arr = np.array([
        [[1, 1],
         [1, 1]],
        [[1, 0],
         [0, 1]]
    ])
    np.testing.assert_array_equal(arr, expected_arr)

def test_trim_incomplete_track_multiple_frames():
    """
    Test with a 3-frame array where only object 1 is present in all frames.
    Other objects (3, 4, 5) appear in only one frame each.
    Expected: objects 3, 4, and 5 are removed.
    """
    # Create a 3-frame, 2x2 array
    arr = np.array([
        [[1, 3],
         [3, 1]],
        [[1, 4],
         [4, 1]],
        [[1, 5],
         [5, 1]]
    ])
    removed_objects = trim_incomplete_track(arr)
    
    # Expect removed objects to be 3, 4, and 5.
    np.testing.assert_array_equal(np.sort(removed_objects), np.array([3, 4, 5]))
    
    # All instances of 3, 4, and 5 should be replaced with 0.
    expected_arr = np.array([
        [[1, 0],
         [0, 1]],
        [[1, 0],
         [0, 1]],
        [[1, 0],
         [0, 1]]
    ])
    np.testing.assert_array_equal(arr, expected_arr)

def test_trim_incomplete_track_no_removal():
    """
    Test with a 2-frame array where all frames contain the same objects.
    Expected: No object is removed and the array remains unchanged.
    """
    arr = np.array([
        [[1, 2],
         [3, 4]],
        [[1, 2],
         [3, 4]]
    ])
    removed_objects = trim_incomplete_track(arr)
    
    # Since every object appears in both frames, the list of removed objects should be empty.
    np.testing.assert_array_equal(removed_objects, np.array([]))
    
    # The original array should remain unchanged.
    expected_arr = np.array([
        [[1, 2],
         [3, 4]],
        [[1, 2],
         [3, 4]]
    ])
    np.testing.assert_array_equal(arr, expected_arr)