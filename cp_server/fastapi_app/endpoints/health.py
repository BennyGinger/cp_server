from fastapi import APIRouter, HTTPException, Request

from cp_server.fastapi_app.endpoints import redis_client

router = APIRouter()

@router.get("/health")
def status():
    return {"message": "FastAPI server is running, and file watcher is initiated."}

@router.get("/health/redis")
def redis_health():
    try:
        if redis_client.ping():
            return {"redis": "ok"}
        raise HTTPException(status_code=503, detail="Redis did not respond to PING")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis error: {e}")

@router.get("/health/celery")
def celery_health(request: Request):
    """
    Pings all registered Celery workers via control.ping().
    Returns 200 if at least one worker responds.
    """
    celery_app = request.app.state.celery_app
    try:
        # ping returns a list of dicts, e.g. [{"worker1@example.com": {"ok": "pong"}}]
        replies = celery_app.control.ping(timeout=5.0)
        if replies:
            return {"celery": "ok", "workers": [list(r.keys())[0] for r in replies]}
        raise HTTPException(status_code=503, detail="No Celery workers responded")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Celery error: {e}")