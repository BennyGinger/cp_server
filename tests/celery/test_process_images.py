from cp_server.tasks_server.celery_tasks import process_images
from cp_server.tasks_server.utils import encode_ndarray_as_bytesb64, decode_bytesb64_to_array


def test_process_images(temp_dir, monkeypatch, img):
    """Test process_images function to ensure the chain executes properly."""
    
    # Create a dummy params
    img_file = temp_dir.joinpath("test_img.tif")
    dst_folder = "output_folder"
    key_label = "refseg"
    settings = {"some_key": {"param1": 1, "param2": 2}}

    # Make sure that imread returns the dummy image.
    monkeypatch.setattr("cp_server.tasks_server.celery_tasks.tiff.imread", lambda f: img)
    
    # Create a mock for the chain that just captures its arguments. Because the real chain is not actually called.
    chain_calls = []
    def fake_chain(*args, **kwargs):
        chain_calls.extend(args)
        class DummyChain:
            def apply_async(self, *args, **kwargs):
                return None
        return DummyChain()
    
    monkeypatch.setattr("cp_server.tasks_server.celery_tasks.chain", fake_chain)

    # Call the function
    result = process_images(settings, img_file, dst_folder, key_label, do_denoise=True,)

    # Verify the return value.
    expected_msg = f"Processing images with workflow {img_file}"
    assert result == expected_msg
    
    # Check that the chain was built with two tasks.
    assert len(chain_calls) == 2

    # Check the arguments of the two tasks.
    remove_bg_sig = chain_calls[0]
    segment_sig = chain_calls[1]
    print(segment_sig.kwargs)

    # Check that remove_bg_sig has the right arguments.
    img_b64 = encode_ndarray_as_bytesb64(img)
    assert remove_bg_sig.args[0] == img_b64
    assert remove_bg_sig.args[1] == img_file
    assert segment_sig.kwargs['settings'] == settings
    
