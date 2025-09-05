import numpy as np

from cp_server.tasks_server.tasks.track.track_utils import stitch_frames


def test_single_frame():
    """
    When there is only one frame, no stitching should occur and the output
    should be identical to the input.
    """
    masks = np.array([[[0, 1],
                       [0, 1]]], dtype=np.int32)
    stitched = stitch_frames(masks.copy())
    np.testing.assert_array_equal(stitched, masks)

def test_two_frames_matching():
    """
    Two frames where the object mask overlaps perfectly should remain with the same label.
    In this case, frame0 and frame1 have the same mask layout.
    """
    frame0 = np.array([[0, 1],
                       [0, 1]], dtype=np.int32)
    frame1 = np.array([[0, 1],
                       [0, 1]], dtype=np.int32)
    masks = np.stack([frame0, frame1])
    
    stitched = stitch_frames(masks.copy())
    # Since the masks overlap, frame1 should retain label 1.
    expected = np.stack([frame0, frame1])
    np.testing.assert_array_equal(stitched, expected)

def test_two_frames_no_overlap():
    """
    When two frames have masks that do not overlap, a new label should be assigned
    to the object in the second frame.
    
    For frame0, the object is on the right, while for frame1, the object is on the left.
    The new label should be assigned starting from mmax+1 (here, mmax is 1 from frame0).
    Thus, frame1's label 1 should be relabeled to 2.
    """
    frame0 = np.array([[0, 1],
                       [0, 1]], dtype=np.int32)
    frame1 = np.array([[1, 0],
                       [1, 0]], dtype=np.int32)
    masks = np.stack([frame0, frame1])
    
    stitched = stitch_frames(masks.copy())
    expected_frame1 = np.array([[2, 0],
                                [2, 0]], dtype=np.int32)
    expected = np.stack([frame0, expected_frame1])
    np.testing.assert_array_equal(stitched, expected)

def test_three_frames_mixed():
    """
    Test with three frames:
    - Frame0: contains one object labeled as 1.
    - Frame1: the object is in the same position as in Frame0 so should keep label 1.
    - Frame2: the object is moved to a non-overlapping location so it should be assigned a new label.
      With mmax = 1 from frame0 and matching in frame1, the new label for frame2 should become 2.
    """
    frame0 = np.array([[0, 1, 1],
                       [0, 1, 1],
                       [0, 0, 0]], dtype=np.int32)
    frame1 = np.array([[0, 1, 1],
                       [0, 1, 1],
                       [0, 0, 0]], dtype=np.int32)
    # Frame2: object is in a different region (non overlapping with frame1).
    frame2 = np.array([[1, 0, 0],
                       [1, 0, 0],
                       [0, 0, 0]], dtype=np.int32)
    masks = np.stack([frame0, frame1, frame2])
    
    stitched = stitch_frames(masks.copy())
    expected_frame2 = np.array([[2, 0, 0],
                                [2, 0, 0],
                                [0, 0, 0]], dtype=np.int32)
    expected = np.stack([frame0, frame1, expected_frame2])
    np.testing.assert_array_equal(stitched, expected)
