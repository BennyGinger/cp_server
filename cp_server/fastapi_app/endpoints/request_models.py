from pathlib import Path
import os
import re
from typing import Any, Union, List

from pydantic import BaseModel, model_validator, Field


# Filename pattern constants
FILENAME_PATTERN = r'^.+_.+_[12]$'
EXPECTED_FORMAT = "<fov_id>_<category>_<round/time_id>.tif where round/time_id is '1' or '2'"


def _validate_filename_pattern(filepath: str, pattern: str, expected_format: str) -> None:
    """
    Helper function to validate filename patterns.
    
    Args:
        filepath (str): The full file path
        pattern (str): The regex pattern to match
        expected_format (str): Human-readable description of expected format
        
    Raises:
        ValueError: If the filename doesn't match the pattern
    """
    path_obj = Path(filepath)
    filename = path_obj.stem
    
    if not re.match(pattern, filename):
        raise ValueError(f"Invalid filename format: {filepath}. Expected format: {expected_format}")


class BackgroundRequest(BaseModel):
    """
    A Pydantic model for background removal requests.
    This model validates the input parameters for background removal tasks.
    Attributes:
        img_path (str | list[str]): Path(s) to the image file(s).
        sigma (float): Sigma value for background subtraction.
        size (int): Size parameter for background subtraction.
    """
    img_path: Union[str, List[str]]
    sigma: float = 0.0
    size: int = 7

    @model_validator(mode="before")
    def validate_img_path(cls, values: dict[str, Any]) -> dict[str, Any]:
        """
        Validate that the file path(s) provided in `img_path` are valid.
        """
        input_file = values.get("img_path")

        if input_file is None:
            raise ValueError("img_path is required")

        def validate_one_path(p):
            if not isinstance(p, (str, bytes, os.PathLike)):
                raise ValueError(f"Provided img_path must be a string or PathLike, got {type(p)}")
            fs_path = os.fsdecode(p)
            input_path = Path(fs_path)
            if not input_path.is_file():
                raise ValueError(f"Provided img_path is not a valid file path: {fs_path}")
            return str(input_path)

        if isinstance(input_file, list):
            values["img_path"] = [validate_one_path(p) for p in input_file]
        else:
            values["img_path"] = validate_one_path(input_file)
        return values

    @model_validator(mode="after")
    def validate_img_filename(self) -> 'BackgroundRequest':
        """
        Validate that the image filename(s) follow the expected naming convention.
        Expected format: <fov_id>_<category>_<round>.<ext>
        """
        if isinstance(self.img_path, list):
            for p in self.img_path:
                _validate_filename_pattern(p, FILENAME_PATTERN, EXPECTED_FORMAT)
        else:
            _validate_filename_pattern(self.img_path, FILENAME_PATTERN, EXPECTED_FORMAT)
        return self

class ProcessRequest(BackgroundRequest):
    """
    A Pydantic model for processing image requests.
    This model validates the input parameters for image processing tasks.
    It ensures that the provided image paths are valid and that the necessary parameters
    for processing are included. Inherits from BackgroundRequest to include background removal parameters.

    Attributes Inherited:
        img_path (str | list[str]): Path(s) to the image file(s).
        sigma (float): Sigma value for background subtraction.
        size (int): Size parameter for background subtraction.

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
    total_fovs: int = Field(exclude=True)
    track_stitch_threshold: float = 0.75
    round: int | None = Field(default=None, exclude=True)

    @model_validator(mode="after")
    def set_round_from_img_path(self) -> 'ProcessRequest':
        # only compute if not provided
        if self.round is None:
            if isinstance(self.img_path, list):
                # Use the first image to determine round
                stem = Path(self.img_path[0]).stem
            else:
                stem = Path(self.img_path).stem
            try:
                # filename format: <fovID>_<category>_<round>
                self.round = int(stem.split("_")[-1])
            except Exception:
                raise ValueError(f"Cannot parse round from img_path '{self.img_path}'")
        return self

    @model_validator(mode="after")
    def validate_well_id(self) -> 'ProcessRequest':
        if not self.well_id:
            raise ValueError("well_id is required for processing")
        return self

    @model_validator(mode="after")
    def validate_dst_folder(self) -> 'ProcessRequest':
        if not self.dst_folder:
            raise ValueError("dst_folder is required for processing")
        dst_folder_path = Path(self.dst_folder)
        if not dst_folder_path.exists():
            dst_folder_path.mkdir(parents=True, exist_ok=True)
        return self

    @model_validator(mode="after")
    def validate_total_fovs(self) -> 'ProcessRequest':
        if self.round == 2 and self.total_fovs is None:
            raise ValueError("total_fovs is required for round 2 processing")
        return self

class RegisterMaskRequest(BaseModel):
    """
    A Pydantic model for registering multiple masks in batch.
    
    Attributes:
        run_id (str): Unique identifier for the processing run.
        mask_paths (list[str]): List of paths to mask files. File names should end with '_1.tif' or '_2.tif'.
        total_fovs (int): Total number of fields of view. It will not be included in the model dump.
        track_stitch_threshold (float, optional): Threshold for stitching masks during tracking. Default to 0.75.
    """
    run_id: str
    mask_paths: list[str]
    total_fovs: int = Field(exclude=True)
    track_stitch_threshold: float = 0.75
    
    @model_validator(mode="before")
    def validate_mask_paths(cls, values: dict[str, Any]) -> dict[str, Any]:
        """
        Validate that the mask paths provided are valid.
        """
        mask_files = values.get("mask_paths")

        if mask_files is None:
            raise ValueError("mask_paths is required")

        if not isinstance(mask_files, list):
            raise ValueError(f"mask_paths must be a list, got {type(mask_files)}")
        
        if not mask_files:
            raise ValueError("mask_paths cannot be empty")

        if not all(isinstance(f, (str, bytes, os.PathLike)) for f in mask_files):
            raise ValueError("All mask paths must be strings or PathLike objects")

        # Validate each file path
        validated_paths = []
        for mask_file in mask_files:
            # Decode the mask file path to a string if it is bytes or os.PathLike
            fs_path = os.fsdecode(mask_file)
            mask_path_obj = Path(fs_path)
            if not mask_path_obj.is_file():
                raise ValueError(f"Provided mask_path is not a valid file path: {fs_path}")
            validated_paths.append(str(mask_path_obj))

        values["mask_paths"] = validated_paths
        return values
    
    @model_validator(mode="after")
    def validate_mask_filenames(self) -> 'RegisterMaskRequest':
        """
        Validate that all mask filenames follow the expected naming convention.
        Expected format: <fov_id>_<category>_<time_id>.tif
        """
        for mask_path in self.mask_paths:
            _validate_filename_pattern(mask_path, FILENAME_PATTERN, EXPECTED_FORMAT)
        return self

class NDArrayPayload(BaseModel):
    """
    A Pydantic model for processing NDArray payloads. This model is used to encapsulate a NumPy ndarray that has been serialized into a JSON-compatible format (e.g., list or nested lists).
    Attributes:
        array (Any): The serialized NumPy ndarray.
        cellpose_settings (dict[str, Any]): Settings for the Cellpose model and segmentation.
    """
    array: str  # base64-encoded JSON string
    cellpose_settings: dict[str, Any]

class NDArrayResult(BaseModel):
    """
    A Pydantic model for returning NDArray results. This model is used to encapsulate a NumPy ndarray that has been serialized into a JSON-compatible format (e.g., list or nested lists).
    Attributes:
        array (Any): The serialized NumPy ndarray.
    """
    array: dict[str, Any]  # dict produced by NumpyJSONEncoder (not double-encoded string)