from typing import Any

from pydantic import BaseModel


class PayLoadWatcher(BaseModel):
    directory: str
    settings: dict[str, dict[str, Any]]
    dst_folder: str
    key_label: str
    do_denoise: bool = True

# Adding src_folder to the payload  
class PayLoadSegement(BaseModel):
    src_folder: str
    directory: str
    settings: dict[str, dict[str, Any]]
    dst_folder: str
    key_label: str
    do_denoise: bool = True
    
    
class PayLoadStopWatcher(BaseModel):
    directory: str
