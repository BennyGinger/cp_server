import asyncio
import logging
from fastapi import APIRouter

from cp_server.logger.consumer_log import consumer_loop
from cp_server.logger.fastapi_logger import configure_fastapi_logger


router = APIRouter()

@router.lifespan("startup")
async def startup_fastapi_logging():
    # 1) Configure FastAPI’s own logger (file + console)
    configure_fastapi_logger()

    # 2) Start the background consumer so Celery logs get re‐emitted locally
    asyncio.create_task(consumer_loop())

    # 3) (Optional) Log a startup message via the standard python logger:
    logging.getLogger("fastapi.startup").info("FastAPI has started; consumer loop active.")