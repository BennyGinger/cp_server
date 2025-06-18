import pytest
np = pytest.importorskip("numpy")

from cp_server.tasks_server.tasks.track.track_utils import trim_incomplete_tracks


def test_single_frame():
    # With a single frame, every object is complete so the mask should remain unchanged.
    mask = np.array([[1, 2], [0, 3]])[None, :, :]  # shape (1, y, x)
    trimmed = trim_incomplete_tracks(mask)
    np.testing.assert_array_equal(trimmed, mask)


def test_complete_tracks():
    # When all objects appear in every frame, the output should match the input.
    mask = np.array([
        [[0, 1],
         [1, 2]],
        [[0, 1],
         [1, 2]]
    ])
    trimmed = trim_incomplete_tracks(mask)
    np.testing.assert_array_equal(trimmed, mask)

def test_incomplete_tracks():
    # Create a mask with two frames where object '2' is missing in the second frame.
    mask = np.array([
        [[1, 2],
         [0, 3]],
        [[1, 0],
         [0, 3]]
    ])
    # The complete objects are 0, 1, and 3. Object 2 should be removed.
    expected = np.array([
        [[1, 0],
         [0, 3]],
        [[1, 0],
         [0, 3]]
    ])
    trimmed = trim_incomplete_tracks(mask)
    np.testing.assert_array_equal(trimmed, expected)
    
def test_original_mask_not_modified():
    # Verify that the original mask array is not modified.
    mask = np.array([
        [[1, 2],
         [0, 3]],
        [[1, 0],
         [0, 3]]
    ])
    mask_copy = mask.copy()
    _ = trim_incomplete_tracks(mask)
    np.testing.assert_array_equal(mask, mask_copy)