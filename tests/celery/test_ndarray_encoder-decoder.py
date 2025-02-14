import pytest
import numpy as np

from cp_server.tasks_server.celery_app import ndarray_encoder, ndarray_decoder


@pytest.mark.parametrize("array", [np.random.randint(0, 65536, (256, 256), dtype=np.uint16),
                                   np.random.randint(0, 65536, (10, 256, 256), dtype=np.uint16)])
def test_ndarray_encoder(array):
    s = ndarray_encoder(array)
    assert isinstance(s, str)
    
@pytest.mark.parametrize("array", [np.random.randint(0, 65536, (256, 256), dtype=np.uint16),
                                   np.random.randint(0, 65536, (10, 256, 256), dtype=np.uint16)])
def test_ndarray_decoder(array):
    s = ndarray_encoder(array)
    arr = ndarray_decoder(s)
    
    assert isinstance(arr, np.ndarray)
    assert np.array_equal(array, arr)
    assert array.shape == arr.shape
    assert array.dtype == arr.dtype