from fastapi import APIRouter

from cp_server.task_server.worker_managment import stop_celery_worker
from cp_server.broker_service.redis_server import stop_redis


router = APIRouter()

@router.get("/")
def status():
    return {"message": "FastAPI server is running with Celery and Redis"}

@router.post("/stop")
def stop_services():
    """Stop Redis and Celery services."""
    stop_celery_worker()
    stop_redis()
    return {"message": "Stopped Celery and Redis services"}