from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from cp_server import logger


router = APIRouter()


class MountDirsRequest(BaseModel):
    src_dir: str
    dst_dir: str
    
@router.post("/mount")
def mount_dirs(request: Request, payload: MountDirsRequest):
    """Mount source and destination directories."""
    
    src_dir = payload.src_dir
    dst_dir = payload.dst_dir
    
    if not Path(src_dir).exists():
        logger.error(f"Source directory does not exist: {src_dir}")
        raise HTTPException(status_code=400, detail="Source directory does not exist")
    if not Path(dst_dir).exists():
        logger.error(f"Destination directory does not exist: {dst_dir}")
        raise HTTPException(status_code=400, detail="Destination directory does not exist")
    
    request.app.state.src_dir = src_dir
    request.app.state.dst_dir = dst_dir
    
    logger.info(f"Source Path mounted: {src_dir} which contains {len(list(Path(src_dir).rglob('*.tif')))} files")
    logger.info(f"Destination Path mounted: {dst_dir} which contains {len(list(Path(dst_dir).rglob('*.tif')))} files")
    
    return {"message": "Source and destination directories mounted",
            "source": src_dir,
            "destination": dst_dir}