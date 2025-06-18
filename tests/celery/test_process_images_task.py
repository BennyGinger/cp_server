# Test for process_images task
import pytest
np = pytest.importorskip("numpy")
tiff = pytest.importorskip("tifffile")
pytest.importorskip("celery")

from cp_server.tasks_server.tasks.celery_main_task import process_images


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
    assert result == f"Image {img_file} was sent to be segmented"
    # Ensure that chain was called with two tasks (remove_bg and segment)
    args = captured_args.get("args", ())
    assert len(args) == 2
    # We check that both elements are celery signatures (they have a "name" attribute)
    assert hasattr(args[0], "name")
    assert hasattr(args[1], "name")



