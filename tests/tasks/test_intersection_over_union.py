import pytest
np = pytest.importorskip("numpy")

from cp_server.tasks_server.tasks.track.track_utils import _intersection_over_union  


def test_iou_identical_masks():
    # When masks are identical, each label should have IOU = 1.
    masks_true = np.array([[0, 1],
                           [1, 1]])
    masks_pred = np.array([[0, 1],
                           [1, 1]])
    # Expected IOU matrix:
    # For label 0: Only the background pixel overlaps: IOU = 1.
    # For label 1: All non-background pixels overlap: IOU = 1.
    expected_iou = np.array([
        [1.0, 0.0],
        [0.0, 1.0]
    ])
    result = _intersection_over_union(masks_true, masks_pred)
    np.testing.assert_allclose(result, expected_iou, rtol=1e-5)

def test_iou_all_background():
    # When both masks contain only background (label 0) the overlap covers the whole image.
    masks_true = np.zeros((3, 3), dtype=int)
    masks_pred = np.zeros((3, 3), dtype=int)
    # Only label 0 is present. Overlap=9, union=9 so IOU = 1.
    expected_iou = np.array([[1.0]])
    result = _intersection_over_union(masks_true, masks_pred)
    np.testing.assert_allclose(result, expected_iou, rtol=1e-5)

def test_iou_partial_overlap():
    # Test a case where there is partial overlap between a single non-background mask.
    masks_true = np.array([
        [0, 1, 1],
        [0, 1, 0],
        [0, 0, 0]
    ])
    masks_pred = np.array([
        [0, 1, 0],
        [0, 1, 1],
        [0, 0, 0]
    ])
    # Manually compute the expected overlap matrix:
    #   For true label 0:
    #       - Overlap with pred label 0: count pixels where both are 0:
    #         positions: (0,0), (1,0), (2,0), (2,1), (2,2) → count = 5.
    #       - Overlap with pred label 1: (1,2) → count = 1.
    #   For true label 1:
    #       - Overlap with pred label 0: (0,2) → count = 1.
    #       - Overlap with pred label 1: positions: (0,1), (1,1) → count = 2.
    #
    # Then, compute the sum over rows and columns:
    #   n_pixels_true[0] = 5 + 1 = 6; n_pixels_true[1] = 1 + 2 = 3.
    #   n_pixels_pred[0] = 5 + 1 = 6; n_pixels_pred[1] = 1 + 2 = 3.
    #
    # The IOU values are computed as:
    #   IOU[0,0] = 5 / (6 + 6 - 5) = 5/7 ≈ 0.7142857
    #   IOU[0,1] = 1 / (6 + 3 - 1) = 1/8 = 0.125
    #   IOU[1,0] = 1 / (3 + 6 - 1) = 1/8 = 0.125
    #   IOU[1,1] = 2 / (3 + 3 - 2) = 2/4 = 0.5
    expected_iou = np.array([
        [5/7, 1/8],
        [1/8, 0.5]
    ], dtype=float)
    
    result = _intersection_over_union(masks_true, masks_pred)
    np.testing.assert_allclose(result, expected_iou, rtol=1e-5)
