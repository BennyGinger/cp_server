from typing import Any

from pydantic import BaseModel


class PayLoad(BaseModel):
    directory: str
    settings: dict[str, dict[str, Any]]
    dst_folder: str
    key_label: str
    do_denoise: bool = True