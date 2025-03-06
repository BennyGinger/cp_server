from watchdog.events import PatternMatchingEventHandler, FileCreatedEvent
from celery import Celery

from cp_server.fastapi_app import logger


class SegmentFileHandler(PatternMatchingEventHandler):
    """Class to handle new images detected to be send to the celery segmentation task"""
    
    def __init__(self, celery_app: Celery, settings: dict, dst_folder: str, key_label: str, do_denoise: bool)-> None:
        # Initialize the handler with the correct patterns and settings.
        super().__init__(patterns=["*.tif"], ignore_directories=True, case_sensitive=False)
        # Store the celery app and settings for later use.
        self.celery_app = celery_app
        self.settings = settings
        self.dst_folder = dst_folder
        self.key_label = key_label
        self.do_denoise = do_denoise

    def on_created(self, event: FileCreatedEvent)-> None:
        logger.info(f"New .tif file detected: {event.src_path}")
        self.celery_app.send_task(
            'cp_server.tasks_server.celery_tasks.process_images',
            kwargs={"settings": self.settings,
                "img_file": event.src_path,
                "dst_folder": self.dst_folder,
                "key_label": self.key_label,
                "do_denoise": self.do_denoise,})

# This handler will be triggered if 2 subsequent masks are detected (i.e. from the same fov). It will recognise the beginning of the file name as unique identifier for the fov.
# This handler will send the masks to the tracking task.
# The tracking task will stitch the masks and trim the incomplete tracks.
# The stitched masks will overwrite the original masks.    
class TrackFileHandler(PatternMatchingEventHandler):
    """Class to handle new masks detected to be send to the celery tracking task"""
    
    def __init__(self, celery_app: Celery, stitch_threshold: float)-> None:
        # Initialize the handler with the correct patterns and settings.
        raise NotImplementedError("This class is not implemented yet.")
        
