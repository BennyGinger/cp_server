from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from cp_server import logger


router = APIRouter()


class MountDirsRequest(BaseModel):
    mnt_dir: str
    
@router.post("/mount")
def mount_dirs(request: Request, payload: MountDirsRequest):
    """Mount source and destination directories."""
    
    mnt_dir = payload.mnt_dir
    
    if not Path(mnt_dir).exists():
        logger.error(f"Source directory does not exist: {mnt_dir}")
        raise HTTPException(status_code=400, detail="Source directory does not exist")
    
    request.app.state.src_dir = mnt_dir
    
    logger.info(f"Source Path mounted: {mnt_dir} which contains {len(list(Path(mnt_dir).rglob('*.tif')))} files")
    
    return {"message": "Source and destination directories mounted",
            "source": mnt_dir,}