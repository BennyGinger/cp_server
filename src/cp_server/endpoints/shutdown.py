import os
import signal
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/shutdown")
async def shutdown()-> JSONResponse:
    def kill_server():
        os.kill(os.getpid(), signal.SIGINT)
    kill_server()
    return JSONResponse(content={"message": "Server shutting down..."})