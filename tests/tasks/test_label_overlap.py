import pytest
np = pytest.importorskip("numpy")

from cp_server.tasks_server.tasks.track.track_utils import _label_overlap


def test_label_overlap_basic():
    # Define two small 2D mask arrays.
    m1 = np.array([[0, 1],
                   [2, 2]])
    m2 = np.array([[0, 1],
                   [1, 2]])
    # Expected overlap matrix explanation:
    # - m1[0,0]=0 and m2[0,0]=0 => overlap[0,0] == 1.
    # - m1[0,1]=1 and m2[0,1]=1 => overlap[1,1] == 1.
    # - m1[1,0]=2 and m2[1,0]=1 => overlap[2,1] == 1.
    # - m1[1,1]=2 and m2[1,1]=2 => overlap[2,2] == 1.
    expected = np.array([[1, 0, 0],
                         [0, 1, 0],
                         [0, 1, 1]], dtype=np.uint)
    result = _label_overlap(m1, m2)
    np.testing.assert_array_equal(result, expected)

def test_label_overlap_all_zeros():
    # Test with arrays containing only zeros.
    m1 = np.zeros((2, 2), dtype=np.int32)
    m2 = np.zeros((2, 2), dtype=np.int32)
    # Since both m1 and m2 contain only label 0, the overlap matrix is 1x1.
    # There are 4 pixels in total.
    expected = np.array([[4]], dtype=np.uint)
    result = _label_overlap(m1, m2)
    np.testing.assert_array_equal(result, expected)

def test_label_overlap_1d_arrays():
    # Test using one-dimensional arrays.
    m1 = np.array([0, 1, 1, 2])
    m2 = np.array([1, 0, 1, 2])
    # Expected overlap:
    # - m1[0]=0, m2[0]=1 -> overlap[0,1] = 1
    # - m1[1]=1, m2[1]=0 -> overlap[1,0] = 1
    # - m1[2]=1, m2[2]=1 -> overlap[1,1] = 1
    # - m1[3]=2, m2[3]=2 -> overlap[2,2] = 1
    expected = np.array([[0, 1, 0],
                         [1, 1, 0],
                         [0, 0, 1]], dtype=np.uint)
    result = _label_overlap(m1, m2)
    np.testing.assert_array_equal(result, expected)

def test_label_overlap_different_ranges():
    # Test with arrays where m1 and m2 have different maximum label values.
    m1 = np.array([0, 1, 2, 2])
    m2 = np.array([1, 3, 0, 3])
    # Expected overlap matrix shape is (max(m1)+1, max(m2)+1) = (3, 4)
    # The counts:
    # - (0,1) occurs once.
    # - (1,3) occurs once.
    # - (2,0) occurs once.
    # - (2,3) occurs once.
    expected = np.array([[0, 1, 0, 0],
                         [0, 0, 0, 1],
                         [1, 0, 0, 1]], dtype=np.uint)
    result = _label_overlap(m1, m2)
    np.testing.assert_array_equal(result, expected)
