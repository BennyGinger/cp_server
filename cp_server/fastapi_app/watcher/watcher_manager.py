import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from celery import Celery
from cp_server.fastapi_app import logger

class FileCreatedHandler(FileSystemEventHandler):
    def __init__(self, celery_app: Celery, settings: dict, dst_folder: str, key_label: str, do_denoise: bool):
        self.celery_app = celery_app
        self.settings = settings
        self.dst_folder = dst_folder
        self.key_label = key_label
        self.do_denoise = do_denoise

    def on_created(self, event):
        # Only act on files, not directories.
        if not event.is_directory:
            logger.info(f"New file detected: {event.src_path}")
            self.celery_app.send_task(
                'cp_server.tasks_server.celery_tasks.process_images',
                kwargs={
                    "settings": self.settings,
                    "img_file": event.src_path,
                    "dst_folder": self.dst_folder,
                    "key_label": self.key_label,
                    "do_denoise": self.do_denoise,
                }
            )

class FileWatcherManager:
    def __init__(self, celery_app: Celery) -> None:
        self.celery_app = celery_app
        self.observer = None

    def start_watcher(self, directory: str, settings: dict, dst_folder: str, key_label: str, do_denoise: bool) -> None:
        path = Path(directory)
        if not path.is_dir():
            logger.error(f"Provided directory does not exist: {directory}")
            raise ValueError("Provided directory does not exist")
        
        event_handler = FileCreatedHandler(self.celery_app, settings, dst_folder, key_label, do_denoise)
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

# Example usage (for testing purposes)
if __name__ == "__main__":
    import sys

    class DummyCelery:
        def __init__(self):
            self.tasks = []

        def send_task(self, name, kwargs):
            self.tasks.append((name, kwargs))
            print("Task sent:", name, kwargs)

    # Set up a dummy celery app and payload
    celery_fake = DummyCelery()
    payload = {
        "settings": {"example": {"option": "value"}},
        "dst_folder": "/tmp",
        "key_label": "test",
        "do_denoise": False,
    }
    directory_to_watch = "/path/to/watch"  # Adjust this path accordingly

    manager = FileWatcherManager(celery_fake)
    try:
        manager.start_watcher(directory_to_watch, **payload)
        # Run indefinitely until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop_watcher()
        sys.exit(0)
