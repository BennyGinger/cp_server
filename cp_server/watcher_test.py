import asyncio
from pathlib import Path
from watchfiles import awatch

async def simple_file_watcher(directory: Path, stop_event: asyncio.Event):
    """
    A minimal file watcher that prints any file changes.
    It stops when stop_event is set.
    """
    async for changes in awatch(directory):
        print("Detected changes:", changes)
        if stop_event.is_set():
            break

async def main(directory: Path):
    # Create an event to signal when to stop the watcher.
    stop_event = asyncio.Event()
    
    # Start the file watcher.
    watcher_task = asyncio.create_task(simple_file_watcher(directory, stop_event))
    print("Watcher started. Create or modify files in the 'watched' directory.")
    
    # Let the watcher run for 10 seconds.
    await asyncio.sleep(10)
    print("Creating new files...")
    for text in ['test.txt', 'test2.txt']:
        new_file = dir.joinpath(text)
        new_file.write_text("Hello World")
    
    # Signal the watcher to stop and wait for it to finish.
    stop_event.set()
    await watcher_task

if __name__ == "__main__":
    
    
    dir = Path("/media/ben/Analysis/Python/Image_tests/src_test")
    asyncio.run(main(dir))
    
    