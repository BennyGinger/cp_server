from fastapi import APIRouter

from cp_server.fastapi_app import get_logger
from cp_server.fastapi_app.endpoints import redis_client


logger = get_logger(__name__)

router = APIRouter()

@router.post("/cleanup/{host_prefix}")
def cleanup_stale_keys(host_prefix: str) -> dict[str, int]:
    """
    Delete any pending or finished keys for this host_prefix.
    E.g. host_prefix='worker-01' will delete:
      pending_tracks:worker-01:*  
      finished:worker-01:*
    Returns the number of keys removed.
    """
    removed = 0
    for prefix in ("pending_tracks:", "finished:"):
        pattern = f"{prefix}{host_prefix}-*"
        for key in redis_client.scan_iter(match=pattern):
            redis_client.delete(key)
            logger.debug(f"Deleted Redis key {key.decode()}")
            removed += 1
    return {"deleted": removed}