# Test for segment task
import numpy as np

from cp_server.tasks_server.tasks.celery_main_task import save_masks_task, segment


def test_save_masks_task(monkeypatch):
    masks = np.zeros((10, 10))
    img_file = "dummy.tif"
    dst_folder = "dummy_folder"
    key_label = "refseg"
    dummy_result = "mask_saved"

    def dummy_save_mask(m, file, folder, label):
        # Check that the parameters are passed correctly
        assert np.array_equal(m, masks)
        assert file == img_file
        assert folder == dst_folder
        assert label == key_label
        return dummy_result

    # Override the imported save_mask function in the task module
    monkeypatch.setattr("cp_server.tasks_server.celery_tasks.save_mask", dummy_save_mask)
    result = save_masks_task(masks, img_file, dst_folder, key_label)
    assert result == dummy_result

def test_segment(monkeypatch):
    img = np.random.rand(10, 10)
    settings = {
        "model": {"param": "value"},
        "segmentation": {"thresh": 0.5},}
    
    img_file = "dummy_seg.tif"
    dst_folder = "dummy_folder"
    key_label = "refseg"
    dummy_masks = np.random.randint(0, 2, (10, 10))

    def dummy_run_seg(s, image, do_denoise):
        assert s == settings
        assert np.array_equal(image, img)
        assert do_denoise is True
        return dummy_masks

    # Patch run_seg
    monkeypatch.setattr("cp_server.tasks_server.celery_tasks.run_seg", dummy_run_seg)

    # Patch save_masks_task.delay to capture its call.
    calls = []
    def dummy_delay(masks, file, folder, label):
        calls.append((masks, file, folder, label))

    monkeypatch.setattr(save_masks_task, "delay", dummy_delay)

    result = segment(img, settings, img_file, dst_folder, key_label, do_denoise=True)
    assert np.array_equal(result, dummy_masks)
    # Verify that save_masks_task.delay was called correctly.
    assert len(calls) == 1
    masks_arg, file_arg, folder_arg, label_arg = calls[0]
    assert np.array_equal(masks_arg, dummy_masks)
    assert file_arg == img_file
    assert folder_arg == dst_folder
    assert label_arg == key_label
