import threading
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from cp_server.fastapi_app import logger


class FileWatcherManager:
    """Class to manage the file watchers for the server."""
    
    def __init__(self) -> None:
        self.observers = {}
        self._lock = threading.RLock()

    def start_watcher(self, directory: str, event_handler: PatternMatchingEventHandler) -> None:
        path = Path(directory)
        if not path.is_dir():
            logger.error(f"Provided directory does not exist: {directory}")
            raise ValueError("Provided directory does not exist")
        
        # Ensure that the observer are thread-safe
        with self._lock:
            if directory in self.observers:
                logger.warning(f"Watcher already exists for directory: {directory}. Restarting it.")
                self.stop_watcher(directory)
            
            observer = Observer()
            observer.schedule(event_handler, str(path), recursive=False)
            observer.start()
            self.observers[directory] = observer
            logger.info(f"Watcher started for directory: {directory}")

    def stop_watcher(self, directory: str) -> None:
        # Get the observer for the directory
        observer = self.observers.get(directory, None)
        
        # If no observer is found, raise an error
        if observer is None:
            logger.warning(f"No watcher found for directory: {directory}")
            raise ValueError("No watcher found for this directory")
        
        # Stop the observer and remove it from the dictionary
        observer.stop()
        observer.join()
        del self.observers[directory]
        logger.info(f"Watcher stopped for directory: {directory}")

    