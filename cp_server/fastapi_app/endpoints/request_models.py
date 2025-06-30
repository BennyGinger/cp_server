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
    
    @model_validator(mode="before")
    def validate_img_path(cls, values: dict[str, Any]) -> dict[str, Any]:
        """
        Validate that the file path provided in `img_path` is valid.
        """
        input_file = values.get("img_path")
        
        if not Path(input_file).is_file():
            raise ValueError(f"Provided img_path is not a valid file path: {input_file}")
        
        return values

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
        cellpose_settings (dict): Model and segmentation settings for Cellpose.
        dst_folder (str): Destination folder where processed images will be saved.
        well_id (str): Unique identifier for the processing well.
        total_fovs (int): Total number of fields of view. It will not be included in the model dump.
        track_stitch_threshold (float, optional): Threshold for stitching masks during tracking. Default to 0.75.
        round (int, optional): The round number for processing, build from the image path if not provided. Defaults to None. It will not be included in the model dump.
    This model uses Pydantic's model validators to ensure that the input files are valid
    and that the necessary parameters are provided.
    """
    cellpose_settings: dict[str, Any]
    dst_folder: str
    well_id: str
    total_fovs: int
    track_stitch_threshold: float = 0.75
    round: int = None

    model_config = ConfigDict(model_dump_exclude={"total_fovs", "round"})
    
    @model_validator(mode="after")
    def set_round_from_img_path(cls, values: dict[str, Any]) -> dict[str, Any]:
        # only compute if not provided
        if values.get("round") is None:
            stem = Path(values["img_path"]).stem
            try:
                # filename format: <fovID>_<category>_<round>
                values["round"] = int(stem.split("_")[-1])
            except Exception:
                raise ValueError(f"Cannot parse round from img_path '{values['img_path']}'")
        return values
    
    @model_validator(mode="after")
    def validate_well_id(cls, values: dict[str, Any]) -> dict[str, Any]:
        well_id = values.get("well_id")
        
        if not well_id:
            raise ValueError("well_id is required for processing")
        
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
    
    
