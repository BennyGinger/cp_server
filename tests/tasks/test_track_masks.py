import numpy as np

from cp_server.tasks_server.tasks.track.track import track_masks


def test_track_masks_complete():
    """
    When a cell (nonzero mask) is present in every frame, the track is complete.
    Therefore, the stitched masks should be identical to the input.
    """
    # Two frames with the same mask: cell labeled '1' appears in both frames.
    frame0 = np.array([[0, 1],
                       [0, 1]], dtype=np.uint16)
    frame1 = np.array([[0, 1],
                       [0, 1]], dtype=np.uint16)
    masks = np.stack([frame0, frame1])
    
    tracked = track_masks(masks.copy(), track_stitch_threshold=0.25)
    # Since the track is complete, the output should be unchanged.
    expected = np.stack([frame0, frame1])
    assert tracked.shape == expected.shape
    np.testing.assert_array_equal(tracked, expected)

def test_track_masks_incomplete():
    """
    When a cell appears only in one frame (i.e. an incomplete track), it should be trimmed.
    Here, the cell labeled '1' appears in frame0 but is missing in frame1.
    Thus, the trimmed result should be background everywhere.
    """
    frame0 = np.array([[0, 1],
                       [0, 1]], dtype=np.int32)
    frame1 = np.zeros((2, 2), dtype=np.int32)  # cell missing in frame1
    masks = np.stack([frame0, frame1])
    
    tracked = track_masks(masks.copy(), track_stitch_threshold=0.25)
    # Incomplete track should be removed (set to background 0 in all frames).
    expected = np.stack([np.zeros((2, 2), dtype=np.int32),
                         np.zeros((2, 2), dtype=np.int32)])
    np.testing.assert_array_equal(tracked, expected)

def test_track_masks_mixed_tracks():
    """
    Test a scenario with two tracks:
    - Track 1 is complete (present in both frames).
    - Track 2 is incomplete (present only in frame0).
    The expected behavior is that only the complete track (label 1) remains.
    """
    # Frame0 has two objects: labels 1 and 2.
    # Frame1 only has label 1.
    frame0 = np.array([[0, 1, 2],
                       [0, 1, 2]], dtype=np.int32)
    frame1 = np.array([[0, 1, 0],
                       [0, 1, 0]], dtype=np.int32)
    masks = np.stack([frame0, frame1])
    
    tracked = track_masks(masks.copy(), track_stitch_threshold=0.25)
    # Only label 1 is present in all frames. Label 2 should be trimmed.
    expected_frame0 = np.array([[0, 1, 0],
                                [0, 1, 0]], dtype=np.int32)
    expected_frame1 = np.array([[0, 1, 0],
                                [0, 1, 0]], dtype=np.int32)
    expected = np.stack([expected_frame0, expected_frame1])
    np.testing.assert_array_equal(tracked, expected)
