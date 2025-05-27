from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, model_validator


class ProcessRequest(BaseModel):
    """
    Payload for an image processing request.
    """
    mod_settings: dict[str, any]
    cp_settings: dict[str, any]
    img_file: str | list[str]
    dst_folder: str
    round: int
    total_fovs: Optional[int] = None
    do_denoise: bool = True
    stitch_threshold: float = 0.75
    sigma: float = 0.0
    size: int = 7
    # List of image paths to be processed, will not be included in the model dump
    image_paths: list[str] = []

    model_config = ConfigDict(model_dump_exclude={"image_paths"})
        
    @model_validator(mode="before")
    def expand_and_validate(cls, values: dict[str, any]) -> dict[str, any]:
        raw = values.get("img_file")
        
        paths: list[str] = []
        if isinstance(raw, str):
            path = Path(raw)
            if path.is_file():
                paths = [str(path)]
            elif path.is_dir():
                paths = [str(p) for p in path.rglob("*.tif") if p.is_file()]
            else:
                raise ValueError(f"Provided img_file path is neither a file nor a directory: {raw}")
            
        elif isinstance(raw, list):
            if not all(Path(p).exists() for p in raw):
                raise ValueError("One or more img_files paths do not exist")
            paths = raw
        else:
            raise ValueError("img_file must be a string or a list of strings")
        
        if not paths:
            raise ValueError("No valid image files found in the provided paths")
        
        values["image_paths"] = paths
        return values
        