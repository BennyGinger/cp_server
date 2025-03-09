from pathlib import Path


def find_project_root(current_path: Path) -> Path:
    """
    Recursively search for the project root directory by looking for the .git directory.
    """
    for parent in current_path.parents:
        if parent.joinpath(".git").exists():
            return parent
    raise FileNotFoundError("Project root with .git directory not found.")

# Ensure logs directory exists at the project root
ROOT_DIR = find_project_root(Path(__file__).resolve())

# Append "logs" folder to the project root
LOGS_DIR = ROOT_DIR.joinpath("logs")  
LOGS_DIR.mkdir(parents=True, exist_ok=True)


# TODO: Separate each celery dockerfile
# TODO: add the save_atomic on the client side:
# def imwrite_atomic(final_path: str, image_data, **kwargs):
#     """
#     Atomically write a TIFF image.
    
#     The image is first written to a temporary file (with a .tmp extension)
#     and then renamed to the final filename. Since os.rename is atomic on the same
#     filesystem, the file watcher will only see the final file once it is completely written.
#     """
#     temp_path = final_path + ".tmp"
#     tifffile.imwrite(temp_path, image_data, **kwargs)
#     os.rename(temp_path, final_path)
# TODO: Implement the tindercells