from typing import Any

from pydantic import BaseModel


class PayLoadSegement(BaseModel):
    """Pydantic model for the segment endpoint"""
    src_folder: str
    directory: str
    settings: dict[str, dict[str, Any]]
    dst_folder: str
    key_label: str
    do_denoise: bool = True

class StartSegmentHandler(BaseModel):
    """Pydantic model for the start_segment_watcher endpoint"""
    directory: str
    settings: dict[str, dict[str, Any]]
    dst_folder: str
    key_label: str
    do_denoise: bool = True
    
class StartTrackingHandler(BaseModel):
    """Pydantic model for the start_tracking_watcher endpoint"""
    directory: str
    stitch_threshold: float
    
class StopDirWatcher(BaseModel):
    """Pydantic model for the stop_segment_watcher endpoint"""
    directory: str
