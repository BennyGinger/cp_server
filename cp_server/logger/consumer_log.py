import asyncio
import json
import logging
import os

import redis

from cp_server.logger.fastapi_logger import LOG_LEVEL


REDIS_HOST     = os.getenv("REDIS_HOST", "redis")
REDIS_PORT     = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB       = int(os.getenv("REDIS_DB", "2"))
LOG_QUEUE_NAME = os.getenv("LOG_QUEUE_NAME", "log_queue")

def configure_consumer_logger() -> logging.Logger:
    """
    Creates (or returns) a logger named "fastapi.consumer" that writes to:
      - stdout  (via StreamHandler)
      - /app/logs/fastapi_combined.log  (via FileHandler)
    In practice, this re-uses the same handlers that FastAPI's root logger already has,
    so we don't need to add duplicates.
    """
    consumer = logging.getLogger("fastapi.consumer")
    consumer.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    return consumer

async def consumer_loop():
    """
    Background task: BRPOP Celery's JSON logs from Redis and re-emit locally so they end up
    in the same file/console as FastAPI's own logs.
    """
    consumer_logger = configure_consumer_logger()

    try:
        client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=False)
        client.ping()
    except redis.exceptions.ConnectionError as e:
        consumer_logger.error(f"Cannot connect to Redis at {REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}: {e}")
        return

    consumer_logger.info(f"Consumer listening on Redis {REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}, queue='{LOG_QUEUE_NAME}'")

    while True:
        try:
            item = client.brpop(LOG_QUEUE_NAME, timeout=5)
            if not item:
                await asyncio.sleep(0)
                continue

            _, raw = item
            record = json.loads(raw.decode("utf-8"))

            name    = record.get("name", "")
            level   = record.get("level", "INFO").upper()
            message = record.get("message", "")
            path    = record.get("pathname")
            ln      = record.get("lineno")

            numeric = getattr(logging, level, logging.INFO)
            # Log under "fastapi.consumer.<original_name>" so you can filter if needed:
            child = logging.getLogger(f"fastapi.consumer.{name}")

            extra = f" ({path}:{ln})" if path and ln else ""
            child.log(numeric, f"{message}{extra}")

        except redis.exceptions.ConnectionError:
            consumer_logger.error("Lost connection to Redis; retrying in 5s")
            await asyncio.sleep(5)
            try:
                client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=False)
                client.ping()
                consumer_logger.info("Reconnected to Redis")
            except Exception:
                continue

        except Exception as e:
            consumer_logger.exception(f"Error in consumer loop: {e}")
            await asyncio.sleep(1)