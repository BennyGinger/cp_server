import asyncio
from pathlib import Path
import warnings

from watchfiles import Change, awatch
from celery import Celery

from cp_server.fastapi_app import logger


class FileWatcherManager:
    def __init__(self, celery_app: Celery)-> None:
        # Store the celery application and a dict to track watchers.
        self.celery_app = celery_app
        # Each key is a directory path; value is a dict with 'task' and 'stop_event'
        self.watchers = {}

    async def file_watcher(self, directory: Path, settings: dict, dst_folder: str, key_label: str, do_denoise:bool, stop_event: asyncio.Event)-> None:
        """
        Watch the given directory for new file creations.
        When a new file is detected, send a Celery task.
        The loop exits gracefully when stop_event is set.
        """
        watcher = awatch(directory)
        while not stop_event.is_set():
            try:
                # Wait for changes with a timeout to periodically check the stop_event.
                changes = await asyncio.wait_for(watcher.__anext__(), timeout=0.5)
            except asyncio.TimeoutError:
                continue  # Check the stop_event again.
            for change, path in changes:
                if change == Change.added:
                    logger.info(f"New file detected: {path}")
                    # Send the Celery task. Adjust 'process_file' as needed.
                    self.celery_app.send_task('cp_server.task_server.celery_task.process_images', 
                                              kwargs={
                                                "settings": settings,
                                                "img_file": Path(path),
                                                "dst_folder": dst_folder,
                                                "key_label": key_label,
                                                "do_denoise": do_denoise,})
                    
        logger.info(f"Watcher for directory {directory} has been stopped.")

    async def start_watcher(self, directory: str, settings: dict, dst_folder: str, key_label: str, do_denoise:bool)-> None:
        """
        Start watching the specified directory.
        Raises a ValueError if the directory is invalid or a watcher is already running.
        """
        directory = Path(directory)
        
        if not directory.is_dir():
            logger.error(f"Provided directory does not exist: {directory}")
            raise ValueError("Provided directory does not exist")
        if str(directory) in self.watchers:
            logger.warning(f"A watcher is already running for this directory: {directory}")
            warnings.warn("A watcher is already running for this directory")
        
        # Create an asyncio event to signal when to stop.
        stop_event = asyncio.Event()
        
        # Create and start the watcher task.
        task = asyncio.create_task(self.file_watcher(directory=directory, 
                                                     settings=settings,
                                                     dst_folder=dst_folder,
                                                     key_label=key_label,
                                                     do_denoise=do_denoise,
                                                     stop_event=stop_event))
        logger.info(f"Watcher started for directory: {directory}")
        logger.debug(f"Task: {task}")
        self.watchers[str(directory)] = {"task": task,
                                         "stop_event": stop_event}

    async def stop_watcher(self, directory: str)-> None:
        """
        Stop watching the specified directory.
        Raises a ValueError if no watcher is found.
        """
        if str(directory) not in self.watchers:
            logger.error(f"No watcher found for this directory: {directory}")
            raise ValueError("No watcher found for this directory")
        watcher_info = self.watchers.pop(directory)
        # Signal the watcher to stop.
        watcher_info["stop_event"].set()
        # Wait for the task to complete.
        await watcher_info["task"]
