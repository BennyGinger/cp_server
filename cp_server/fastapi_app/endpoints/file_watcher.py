import asyncio
from celery import Celery
from fastapi import APIRouter, HTTPException, Request

from cp_server.fastapi_app.watcher.watcher_manager import FileWatcherManager
from cp_server.fastapi_app.watcher.event_handler import SegmentFileHandler
from cp_server.fastapi_app.endpoints.utils import PayLoadWatcher, PayLoadStopWatcher

router = APIRouter()


@router.post("/setup-file-watcher")
async def setup_segment_watcher(request: Request, payload: PayLoadWatcher) -> dict:
    # Get the watcher manager and celery_app from the app state
    watcher_manager: FileWatcherManager = request.app.state.watcher_manager
    celery_app: Celery = request.app.state.celery_app
    
    # Initialize the file handler:
    event_handler = SegmentFileHandler(celery_app=celery_app, 
                                       settings=payload.settings, 
                                       dst_folder=payload.dst_folder, 
                                       key_label=payload.key_label, 
                                       do_denoise=payload.do_denoise)
    
    # Start the watcher
    try:
        #watcher_manager.start_watcher(**payload.model_dump())
        await asyncio.to_thread(watcher_manager.start_watcher, 
                                directory=payload.directory, 
                                event_handler=event_handler)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": f"File watcher setup for directory: {payload.directory}"}

@router.post("/stop-file-watcher")
async def stop_file_watcher(request: Request, payload: PayLoadStopWatcher) -> dict:
    # Get the watcher manager from the app state
    watcher_manager: FileWatcherManager = request.app.state.watcher_manager
    
    # Stop the watcher
    try:
        await asyncio.to_thread(watcher_manager.stop_watcher, directory=payload.directory)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": f"File watcher stopped for directory: {payload.directory}"}
