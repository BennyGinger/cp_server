# Test for process_images task
import numpy as np
import tifffile as tiff

from cp_server.tasks_server.tasks.celery_main_task import process_images


def test_process_images(monkeypatch):
    # cellpose settings structure
    settings = {
        "model": {"param": "value"},
        "segmentation": {"thresh": 0.5},
    }

    img_file = "dummy_process.tif"
    dst_folder = "dummy_folder"
    key_label = "refseg"
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

    # Patch the `chain` symbol imported in the module under test
    monkeypatch.setattr("cp_server.tasks_server.tasks.celery_main_task.chain", dummy_chain)

    # Call process_images with current signature: img_path, cellpose_settings, dst_folder, well_id
    result = process_images(
        img_file,
        settings,
        dst_folder,
        key_label,
    )
    assert result == f"Image {img_file} was sent to be segmented"
    # Ensure that chain was called with three tasks (remove_bg, segment, counter)
    args = captured_args.get("args", ())
    assert len(args) == 3
    # We check that both elements are celery signatures (they have a "name" attribute)
    assert hasattr(args[0], "name")
    assert hasattr(args[1], "name")



