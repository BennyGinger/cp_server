from unittest.mock import MagicMock

from watchdog.events import FileCreatedEvent

from cp_server.fastapi_app.watcher.event_handlers import SegmentFileHandler


def test_segment_file_handler_on_created():
    """Test that SegmentFileHandler calls celery_app.send_task with the correct parameters."""
    # Create a dummy celery app with a MagicMock for send_task.
    dummy_celery_app = MagicMock()
    settings = {"foo": "bar"}
    dst_folder = "/destination"
    key_label = "key"
    do_denoise = True

    handler = SegmentFileHandler(
        celery_app=dummy_celery_app,
        settings=settings,
        dst_folder=dst_folder,
        key_label=key_label,
        do_denoise=do_denoise)

    # Create a dummy file creation event.
    event = FileCreatedEvent("/path/to/file.tif")
    handler.on_created(event)

    dummy_celery_app.send_task.assert_called_once_with(
        'cp_server.tasks_server.celery_tasks.process_images',
        kwargs={
            "settings": settings,
            "img_file": event.src_path,
            "dst_folder": dst_folder,
            "key_label": key_label,
            "do_denoise": do_denoise,})
    
    # Retrieve the call arguments.
    call_args, call_kwargs = dummy_celery_app.send_task.call_args

    # The first positional argument should be the task name.
    task_name = call_args[0]
    assert task_name == 'cp_server.tasks_server.celery_tasks.process_images'

    # The kwargs passed to send_task should include our expected "kwargs" dict.
    expected_kwargs = {
        "settings": settings,
        "img_file": event.src_path,
        "dst_folder": dst_folder,
        "key_label": key_label,
        "do_denoise": do_denoise,}
    
    # Since send_task is called with a keyword argument 'kwargs', we check that:
    assert "kwargs" in call_kwargs
    assert call_kwargs["kwargs"] == expected_kwargs