from typing import Optional

from celery import shared_task

from cp_server.tasks_server import get_logger
from cp_server.tasks_server.utils.redis_com import redis_client, RedisError
from cp_server.tasks_server.tasks.track.track_task import track_cells


logger = get_logger('counter_tasks')

@shared_task(name="cp_server.tasks_server.tasks.counter.counter_task_manager.mark_one_done")
def mark_one_done(run_id: str) -> Optional[str]:
    """
    Celery callback: decrement the pending counter; if zero, fire final task.
    """
    remaining = redis_client.decr(f"pending_tracks:{run_id}")
    logger.info(f"Tracks remaining: {remaining}")
    if remaining == 0:
        all_tracks_finished.delay(run_id)

@shared_task(name="cp_server.tasks_server.tasks.counter.counter_task_manager.all_tracks_finished")
def all_tracks_finished(run_id: str) -> str:
    """
    Runs once when the last track_cells completes for this run_id.
    """
    # 1) Delete the pending counter
    logger.info(f"All tracking done for all FOVs for {run_id}")
    redis_client.delete(f"pending_tracks:{run_id}")  # Clear the pending counter
    
    # 2) Delete all per-FOV hashes
    pattern = f"masks:{run_id}:*"
    for key in redis_client.scan_iter(match=pattern):
        redis_client.delete(key)
        logger.debug(f"Deleted Redis key {key.decode()}")
    
    # 3) Create a finish flag
    finish_key = f"finished:{run_id}"
    redis_client.set(finish_key, 1)
    redis_client.expire(finish_key, 12 * 3600) # Set an expiration time of 12 hours
    
    return f"Run {run_id} completed successfully. All tracks finished."  

@shared_task(name="cp_server.tasks_server.tasks.counter.counter_task_manager.check_and_track")
def check_and_track(hkey: str, stitch_threshold: float) -> None:
    """
    Check if there are two masks for the same FOV in Redis. If so, trigger the tracking task.
    Wrapped in try/except to catch Redis errors.
    """
    try:
        # 1) See how many masks we have
        count = redis_client.hlen(hkey)
        logger.debug(f"Redis hlen({hkey}) = {count}")

        if count == 2:
            # 2) Parse run_id and fov_id out of the key name
            _, run_id, fov_id = hkey.split(":", 2)

            # 3) Grab the two mask paths
            raw_vals = redis_client.hvals(hkey)
            paths = [p.decode() for p in raw_vals]
            logger.info(f"Found 2 masks for {fov_id} in run {run_id}: {paths}")

            # 4) Clean up the hash so we don't double-track
            redis_client.delete(hkey)
            logger.debug(f"Deleted Redis hash {hkey}")

            # 5) Fire off tracking, with a safe callback
            track_cells.apply_async(
                args=[paths, stitch_threshold],
                link=mark_one_done.si(run_id))

    except RedisError as e:
        # Log full stack so you know what happened
        logger.exception(f"Redis error in check_and_track for key {hkey}: {e}")
        # Re-raise if you want Celery to retry this task
        raise

    except Exception as e:
        # Catch anything else unexpected
        logger.exception(f"Unexpected error in check_and_track for key {hkey}: {e}")
        raise    