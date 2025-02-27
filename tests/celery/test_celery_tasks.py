import numpy as np
import tifffile as tiff

from cp_server.tasks_server.celery_tasks import (
    save_masks_task,
    save_img_task,
    remove_bg,
    segment,
    process_images)

# Test for save_masks_task
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

# Test for save_img_task
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

# Test for remove_bg task
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

# Test for segment task
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

# Test for process_images task
def test_process_images(monkeypatch):
    settings = {
        "model": {"param": "value"},
        "segmentation": {"thresh": 0.5},}
    
    img_file = "dummy_process.tif"
    dst_folder = "dummy_folder"
    key_label = "refseg"
    do_denoise = True
    dummy_img = np.ones((10, 10))

    # Patch tiff.imread to return a dummy image
    monkeypatch.setattr(tiff, "imread", lambda file: dummy_img if file == img_file else None)

    # Patch chain to capture the arguments and simulate the asynchronous chain call.
    captured_args = {}

    def dummy_chain(*args, **kwargs):
        captured_args["args"] = args
        class DummyChain:
            def apply_async(self):
                return "chain_applied"
        return DummyChain()

    monkeypatch.setattr("cp_server.tasks_server.celery_tasks.chain", dummy_chain)

    result = process_images(
        settings,
        img_file,
        dst_folder,
        key_label,
        do_denoise=do_denoise,
        extra_kwarg="value",
    )
    assert result == f"Processing images with workflow {img_file}"
    # Ensure that chain was called with two tasks (remove_bg and segment)
    args = captured_args.get("args", ())
    assert len(args) == 2
    # We check that both elements are celery signatures (they have a "name" attribute)
    assert hasattr(args[0], "name")
    assert hasattr(args[1], "name")
