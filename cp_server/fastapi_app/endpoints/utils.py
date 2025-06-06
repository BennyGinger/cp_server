from pathlib import Path
from typing import Optional, Any

from pydantic import BaseModel, ConfigDict, model_validator


class ProcessRequest(BaseModel):
    """
    A Pydantic model for processing image requests.
    This model validates the input parameters for image processing tasks.
    It ensures that the provided image paths are valid and that the necessary parameters
    for processing are included.
    Attributes:
        mod_settings (dict): Settings for the model.
        cp_settings (dict): Settings for the Cellpose processing.
        img_file (str | list[str]): Path to an image file, a directory containing images, or a list of image paths.
        dst_folder (str): Destination folder where processed images will be saved.
        round (int): The round number for processing.
        run_id (str): Unique identifier for the processing run.
        total_fovs (Optional[int]): Total number of fields of view, if applicable. It will not be included in the model dump.
        do_denoise (bool): Whether to apply denoising (default is True).
        stitch_threshold (float): Threshold for stitching masks (default is 0.75).
        sigma (float): Sigma value for background subtraction (default is 0.0).
        size (int): Size parameter for background subtraction (default is 7).
        image_paths (list[str]): List of image paths to be processed, will not be included in the model dump.
    This model uses Pydantic's model validators to ensure that the input files are valid
    and that the necessary parameters are provided.
    """
    mod_settings: dict[str, Any]
    cp_settings: dict[str, Any]
    img_file: str | list[str]
    dst_folder: str
    round: int
    run_id: str
    total_fovs: Optional[int] = None
    do_denoise: bool = True
    stitch_threshold: float = 0.75
    sigma: float = 0.0
    size: int = 7
    # List of image paths to be processed, will not be included in the model dump
    image_paths: list[str] = []

    model_config = ConfigDict(model_dump_exclude={"image_paths", "total_fovs"})
        
    @model_validator(mode="before")
    def validate_input_files(cls, values: dict[str, Any]) -> dict[str, Any]:
        input_files = values.get("img_file")
        
        paths: list[str] = []
        if isinstance(input_files, str):
            paths = cls._get_image_paths(input_files)
            
        elif isinstance(input_files, list):
            if not all(Path(p).exists() for p in input_files):
                raise ValueError("One or more img_files paths do not exist")
            paths = input_files
        else:
            raise ValueError("img_file must be a string or a list of strings")
        
        if not paths:
            raise ValueError("No valid image files found in the provided paths")
        
        values["image_paths"] = paths
        
        return values

    @model_validator(mode="after")
    def validate_run_id(cls, values: dict[str, Any]) -> dict[str, Any]:
        run_id = values.get("run_id")
        
        if not run_id:
            raise ValueError("run_id is required for processing")
        
        return values
    
    @model_validator(mode="after")
    def validate_dst_folder(cls, values: dict[str, Any]) -> dict[str, Any]:
        dst_folder = values.get("dst_folder")
        
        if not dst_folder:
            raise ValueError("dst_folder is required for processing")
        
        dst_folder_path = Path(dst_folder)
        if not dst_folder_path.exists():
            dst_folder_path.mkdir(parents=True, exist_ok=True)
        
        return values
    
    @model_validator(mode="after")
    def validate_total_fovs(cls, values: dict[str, Any]) -> dict[str, Any]:
        total_fovs = values.get("total_fovs")
        if values.get("round") == 2 and total_fovs is None:
            raise ValueError("total_fovs is required for round 2 processing")
        
        return values
    
    @classmethod
    def _get_image_paths(cls, input_files: str) -> list[str]:
        path = Path(input_files)
        if path.is_file():
            paths = [str(path)]
        elif path.is_dir():
            paths = [str(p) for p in path.rglob("*.tif") if p.is_file()]
        else:
            raise ValueError(f"Provided img_file path is neither a file nor a directory: {input_files}")
        return paths