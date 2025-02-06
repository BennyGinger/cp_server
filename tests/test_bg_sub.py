import numpy as np
import pytest

from cp_server.task_server.tasks.bg_sub.bg_sub import apply_bg_sub


@pytest.fixture
def img():
    return np.random.randint(0, 65536, (256, 256), dtype=np.uint16)


def test_apply_bg_sub(img):
    
    bg_img = apply_bg_sub(img)
    
    assert bg_img.shape == img.shape
    assert bg_img.dtype == img.dtype
    assert np.all(bg_img >= 0)
    assert not np.array_equal(bg_img, img), "The background-subtracted image should be different from the original image"