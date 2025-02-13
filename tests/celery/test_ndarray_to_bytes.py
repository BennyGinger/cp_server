import pytest

from cp_server.tasks_server.utils import *


def test_ndarray_to_bytes(img):
    arr_bytes = ndarray_to_bytes(img)
    assert isinstance(arr_bytes, bytes)
    
def test_bytes_to_ndarray(img):
    arr_bytes = ndarray_to_bytes(img)
    arr = bytes_to_ndarray(arr_bytes)
    assert isinstance(arr, np.ndarray)
    assert np.array_equal(img, arr)
    assert img.shape == arr.shape
    assert img.dtype == arr.dtype
    
def test_ndarray_to_b64(img):
    b64_str = encode_ndarray_as_bytesb64(img)
    assert isinstance(b64_str, str)

@pytest.mark.parametrize("array", [np.random.randint(0, 65536, (256, 256), dtype=np.uint16),
                                   np.random.randint(0, 65536, (10, 256, 256), dtype=np.uint16)])
def test_b64_to_ndarray(array):
    b64_str = encode_ndarray_as_bytesb64(array)
    arr = decode_bytesb64_to_array(b64_str)
    assert isinstance(arr, np.ndarray)
    assert np.array_equal(array, arr)
    assert array.shape == arr.shape
    assert array.dtype == arr.dtype