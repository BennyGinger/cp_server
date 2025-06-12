from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class BackgroundRequest(BaseModel):
    """
    A Pydantic model for background removal requests.
    This model validates the input parameters for background removal tasks.
    Attributes:
        img_path (str): Path to the image file.
        sigma (float): Sigma value for background subtraction.
        size (int): Size parameter for background subtraction.
    """
    img_path: str
    sigma: float = 0.0
    size: int = 7
    # List of image paths to be processed, will not be included in the model dump
    image_paths: list[str] = []

    model_config = ConfigDict(model_dump_exclude={"image_paths"})
    
    @model_validator(mode="before")
    def validate_input_files(cls, values: dict[str, Any]) -> dict[str, Any]:
        """
        Validate the input files provided in img_file.
        This method checks if the img_file is a string or a list of strings,
        and retrieves the paths of the images to be processed.
        The newly formed image_paths list is used to send each file to the processing task.
        It will not be included in the model dump.
        Raises:
            ValueError: If img_file is not a string or a list of strings,
                        or if the provided paths do not exist.
            ValueError: If no valid image files are found in the provided paths.
        """
        input_files = values.get("img_path")
        
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

class ProcessRequest(BackgroundRequest):
    """
    A Pydantic model for processing image requests.
    This model validates the input parameters for image processing tasks.
    It ensures that the provided image paths are valid and that the necessary parameters
    for processing are included. Inherits from BackgroundRequest to include background removal parameters.
    
    Attributes Inherited:
        img_path (str): Path to the image file.
        sigma (float): Sigma value for background subtraction.
        size (int): Size parameter for background subtraction.
        image_paths (list[str]): List of image paths to be processed, will not be included in the model dump.
    
    Attributes:
        mod_settings (dict): Settings for the model.
        cp_settings (dict): Settings for the Cellpose processing.
        dst_folder (str): Destination folder where processed images will be saved.
        round (int): The round number for processing.
        run_id (str): Unique identifier for the processing run.
        segment_and_track (bool): Whether to perform segmentation and tracking (default is False).
        total_fovs (Optional[int]): Total number of fields of view, if applicable. It will not be included in the model dump.
        do_denoise (bool): Whether to apply denoising (default is True).
        track_stitch_threshold (float): Threshold for stitching masks (default is 0.75).
    This model uses Pydantic's model validators to ensure that the input files are valid
    and that the necessary parameters are provided.
    """
    mod_settings: dict[str, Any]
    cp_settings: dict[str, Any]
    dst_folder: str
    round: int
    run_id: str
    segment_and_track: bool = False
    total_fovs: int = None
    do_denoise: bool = True
    track_stitch_threshold: float = 0.75

    model_config = ConfigDict(model_dump_exclude={"image_paths", "total_fovs"})
        
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
    
    
