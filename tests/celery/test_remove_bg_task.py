import pytest
np = pytest.importorskip("numpy")
pytest.importorskip("celery")

from cp_server.tasks_server.tasks.celery_main_task import save_img_task, remove_bg


def test_save_img_task(monkeypatch):
    img = np.ones((10, 10))
    img_file = "dummy_img.tif"
    dummy_result = "img_saved"

    def dummy_save_img(image, file):
        assert np.array_equal(image, img)
        assert file == img_file
        return dummy_result

    monkeypatch.setattr("cp_server.tasks_server.celery_tasks.save_img", dummy_save_img)
    result = save_img_task(img, img_file)
    assert result == dummy_result

def test_remove_bg(monkeypatch):
    img = np.random.rand(10, 10)
    img_file = "dummy.tif"
    dummy_bg = np.random.rand(10, 10)

    def dummy_apply_bg_sub(image, **kwargs):
        assert np.array_equal(image, img)
        return dummy_bg

    # Patch the apply_bg_sub function
    monkeypatch.setattr("cp_server.tasks_server.celery_tasks.apply_bg_sub", dummy_apply_bg_sub)

    # Patch save_img_task.delay so we can capture its call without actually scheduling it.
    # Patch save_img_task.delay to capture its call without scheduling it.
    calls = []
    def dummy_delay(image, file):
        calls.append((image, file))

    # Instead of replacing the entire task, override only its delay method.
    monkeypatch.setattr(save_img_task, "delay", dummy_delay)

    result = remove_bg(img, img_file, extra_param="value")
    assert np.array_equal(result, dummy_bg)
    # Ensure that save_img_task.delay was called with the right arguments.
    assert len(calls) == 1
    called_img, called_file = calls[0]
    assert np.array_equal(called_img, dummy_bg)
    assert called_file == img_file




