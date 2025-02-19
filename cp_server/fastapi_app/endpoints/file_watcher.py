import asyncio
from fastapi import APIRouter, HTTPException, Request

from cp_server.fastapi_app.watcher.watcher_manager import FileWatcherManager
from cp_server.fastapi_app.endpoints.utils import PayLoadWatcher

router = APIRouter()


@router.post("/setup-file-watcher")
async def setup_file_watcher(request: Request, payload: PayLoadWatcher) -> dict:
    watcher_manager: FileWatcherManager = request.app.state.watcher_manager
    try:
        watcher_manager.start_watcher(**payload.model_dump())
        #await asyncio.to_thread(watcher_manager.start_watcher, **payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": f"File watcher setup for directory: {payload.directory}"}

@router.post("/stop-file-watcher")
async def stop_file_watcher(request: Request, directory: str) -> dict:
    watcher_manager: FileWatcherManager = request.app.state.watcher_manager
    try:
        watcher_manager.stop_watcher()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": f"File watcher stopped for directory: {directory}"}
