from collections import defaultdict
from pathlib import Path
import re
import logging

from watchdog.events import PatternMatchingEventHandler, FileCreatedEvent
from celery import Celery


# Setup logging
logger = logging.getLogger("cp_server.fastapi_app")


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
        
        logger.info(f"Sent image to segmentation task: {event.src_path}")

class TrackFileHandler(PatternMatchingEventHandler):
    """This handler will be triggered if 2 subsequent masks are detected (i.e. from the same fov). The fov_id is used as unique identifier for the fov. It will send the masks to the tracking task and overwrite the original masks."""
    
    def __init__(self, celery_app: Celery, stitch_threshold: float)-> None:
        # Initialize the handler with the correct patterns and settings.
        super().__init__(patterns=["*_mask_*.tif"], ignore_directories=True, case_sensitive=False)
        self.celery_app = celery_app
        self.stitch_threshold = stitch_threshold
        
        # Dictionary to keep track of the masks that are detected.
        # Dictionary structure: { fov_id: { '1': filename1, '2': filename2 } }
        self.mask_files = defaultdict(dict)
        
        # Reg ex pattern to extract the fov_id and time_id from the filename.
        self.pattern = re.compile(r"^(?P<fov_id>[A-Z]\d{1,2}_P\d{1,4})_.*?_(?P<time_id>[1-2])\.tif$")
        
    def on_created(self, event: FileCreatedEvent) -> None:
        logger.info(f"New mask file detected: {event.src_path}")

        # Extract the fov_id and time_id from the filename.
        filename = Path(event.src_path).name
        match = self.pattern.match(filename)
        if match is None:
            logger.error(f"Could not extract fov_id and time_id from filename: {filename}")
            return
        
        fov_id = match.group('fov_id')
        time_id = match.group('time_id')
        
        # Update the mask_files dictionary with the new mask.
        self.mask_files[fov_id][time_id] = event.src_path
        
        # Check if we have 2 masks for the same fov.
        if set(self.mask_files[fov_id].keys()) == {'1', '2'}:
            # Pack the masks in the correct order.
            img_files = [self.mask_files[fov_id]['1'], self.mask_files[fov_id]['2']]
            
            # Send the masks to the tracking task.
            self.celery_app.send_task(
                'cp_server.tasks_server.celery_tasks.track_cells',
                kwargs={"img_files": img_files,
                        "stitch_threshold": self.stitch_threshold})

            # Clear the mask_files dictionary for this fov.
            self.mask_files[fov_id].clear()
            logger.info(f"Sent masks to tracking task for fov: {fov_id}")
        else:
            logger.info(f"Detected mask for fov: {fov_id} and time: {time_id}")
            logger.info(f"Waiting for the second mask to be detected.")
        
