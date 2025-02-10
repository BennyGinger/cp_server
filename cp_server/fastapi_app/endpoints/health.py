from fastapi import APIRouter


router = APIRouter()

@router.get("/health")
def status():
    return {"message": "FastAPI server is running with Celery and Redis"}

