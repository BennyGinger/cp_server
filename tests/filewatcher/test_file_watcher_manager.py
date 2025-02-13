import asyncio

import pytest

from cp_server.fastapi_app.watcher.watcher_manager import FileWatcherManager


@pytest.mark.asyncio
async def test_invalid_directory(tmp_path, fake_celery, payload):
    """
    Test that starting a watcher on a non-existent directory raises ValueError.
    """
    manager = FileWatcherManager(fake_celery)
    # Use a path that does not exist.
    invalid_directory = tmp_path.joinpath("nonexistent")
    payload["directory"] = str(invalid_directory)
    # Attempt to start the watcher.
    with pytest.raises(ValueError):
        await manager.start_watcher(**payload)
            

@pytest.mark.asyncio
async def test_start_and_stop_watcher(tmp_path, fake_celery, payload):
    """
    Test starting and then stopping the watcher.
    """
    manager = FileWatcherManager(fake_celery)
    # Create a temporary directory for watching.
    directory = tmp_path.joinpath("watch_dir")
    directory.mkdir()
    payload["directory"] = str(directory)
    await manager.start_watcher(**payload)
    
    # Confirm that the watcher was added.
    assert str(directory) in manager.watchers

    # Stop the watcher.
    await manager.stop_watcher(str(directory))
    
    # Confirm that the watcher has been removed.
    assert str(directory) not in manager.watchers


@pytest.mark.asyncio
async def test_watcher_detects_new_file(tmp_path, fake_celery, payload):
    """
    Test that when a new file is created in the watched directory, the celery task is sent.
    """
    manager = FileWatcherManager(fake_celery)
    directory = tmp_path.joinpath("watch_dir")
    directory.mkdir()
    payload["directory"] = str(directory)
    print(f"{payload=}")
    await manager.start_watcher(**payload)
    # Wait briefly to ensure the watcher loop is active.
    await asyncio.sleep(10)

    # Create a new file in the directory.
    new_file = directory.joinpath("test.txt")
    print(f"{new_file=}")
    new_file.write_text("Hello World")
    assert new_file.exists()
    
    # Stop the watcher.
    await asyncio.sleep(2)
    await manager.stop_watcher(str(directory))

    # Check that send_task was called with the correct parameters.
    # Since file events might be picked up more than once,
    # we simply verify that one of the tasks matches our expectation.
    found = False
    print(f"{manager.celery_app.tasks=}")
    for task in manager.celery_app.tasks:
        _, kwargs = task
        print(kwargs)
        if kwargs.get("img_file") == str(new_file):
            found = True
            assert kwargs["settings"] == payload["settings"]
            assert kwargs["dst_folder"] == payload['dst_folder']
            assert kwargs["key_label"] == payload['key_label']
            assert kwargs["do_denoise"] == payload['do_denoise']
    assert found, "The new file was not processed by the watcher."


@pytest.mark.asyncio
async def test_stop_nonexistent_watcher(tmp_path, fake_celery):
    """
    Test that stopping a watcher for a directory that is not being watched raises ValueError.
    """
    manager = FileWatcherManager(fake_celery)
    non_existing = tmp_path.joinpath("nonexistent")
    with pytest.raises(ValueError):
        await manager.stop_watcher(str(non_existing))


@pytest.mark.asyncio
async def test_duplicate_watcher_warning(tmp_path, fake_celery, payload):
    """
    Test that starting a watcher on a directory that is already being watched produces a warning.
    """
    manager = FileWatcherManager(fake_celery)
    directory = tmp_path.joinpath("watch_dir")
    directory.mkdir()
    payload["directory"] = str(directory)
    
    # Start the watcher the first time.
    await manager.start_watcher(**payload)

    # Attempt to start the watcher again for the same directory.
    with pytest.warns(UserWarning):
        await manager.start_watcher(**payload)

    # Stop the watcher.
    await manager.stop_watcher(str(directory))
    
