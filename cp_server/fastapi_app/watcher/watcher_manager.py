import time
import os
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler, FileCreatedEvent
from pathlib import Path
from celery import Celery
from cp_server.fastapi_app import logger

def is_file_stable(filepath: str, interval: int=1, retries: int=10)-> bool:
    """Check if file size remains the same over a given interval."""
    previous_size = -1
    for _ in range(retries):
        current_size = os.path.getsize(filepath)
        if current_size != previous_size:
            previous_size = current_size
            time.sleep(interval)
        else:
            return True
    return False

class TifFileHandler(PatternMatchingEventHandler):
    def __init__(self, celery_app: Celery, settings: dict, dst_folder: str, key_label: str, do_denoise: bool):
        super().__init__(patterns=["*.tif"], ignore_directories=True, case_sensitive=False)
        self.celery_app = celery_app
        self.settings = settings
        self.dst_folder = dst_folder
        self.key_label = key_label
        self.do_denoise = do_denoise

    def on_created(self, event: FileCreatedEvent)-> None:
        logger.info(f"New .tif file detected: {event.src_path}")
        if is_file_stable(event.src_path):
            self.celery_app.send_task(
                'cp_server.tasks_server.celery_tasks.process_images',
                kwargs={"settings": self.settings,
                        "img_file": event.src_path,
                        "dst_folder": self.dst_folder,
                        "key_label": self.key_label,
                        "do_denoise": self.do_denoise,})
        else:
            logger.error(f"File {event.src_path} did not stabilize, skipping processing.")

class FileWatcherManager:
    def __init__(self, celery_app: Celery) -> None:
        self.celery_app = celery_app
        self.observer = None

    def start_watcher(self, directory: str, settings: dict, dst_folder: str, key_label: str, do_denoise: bool) -> None:
        path = Path(directory)
        if not path.is_dir():
            logger.error(f"Provided directory does not exist: {directory}")
            raise ValueError("Provided directory does not exist")
        
        event_handler = TifFileHandler(self.celery_app, settings, dst_folder, key_label, do_denoise)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(path), recursive=False)
        self.observer.start()
        logger.info(f"Watcher started for directory: {directory}")

    def stop_watcher(self) -> None:
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("Watcher stopped.")
        else:
            logger.warning("No watcher to stop.")
