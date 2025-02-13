import asyncio
import pytest
from pathlib import Path
from watchfiles import awatch

async def simple_file_watcher(directory: Path, stop_event: asyncio.Event, events: list):
    async for changes in awatch(directory):
        events.append(changes)
        if stop_event.is_set():
            break

@pytest.mark.asyncio
async def test_simple_file_watcher(tmp_path):
    events = []
    directory = tmp_path / "watch_dir"
    directory.mkdir()
    
    stop_event = asyncio.Event()
    watcher = asyncio.create_task(simple_file_watcher(directory, stop_event, events))
    
    # Wait briefly to ensure the watcher is running.
    await asyncio.sleep(0.5)
    
    # Create a new file in the directory.
    new_file = directory / "test.txt"
    new_file.write_text("Hello, world!")
    
    # Allow time for the watcher to detect the new file.
    await asyncio.sleep(1)
    
    # Signal the watcher to stop.
    stop_event.set()
    await watcher

    # Verify that at least one event mentions the new file.
    detected = any(
        any(new_file.name in str(path) for (_, path) in change_group)
        for change_group in events
    )
    assert detected, "The new file event was not detected by the watcher."
