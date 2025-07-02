from typing import Optional, List

from celery import shared_task

from cp_server.tasks_server import get_logger
from cp_server.tasks_server.utils.redis_com import redis_client
from cp_server.tasks_server.celery_app import celery_app
from redis import RedisError


logger = get_logger('counter_tasks')

@shared_task(name="cp_server.tasks_server.tasks.counter.counter_task_manager.mark_one_done")
def mark_one_done(well_id: str) -> Optional[str]:
    """
    Celery callback: decrement the pending counter; if zero, fire final task.
    """
    remaining = redis_client.decr(f"pending_tracks:{well_id}")
    logger.info(f"Tracks remaining: {remaining}")
    if remaining == 0:
        celery_app.send_task(
            'cp_server.tasks_server.tasks.counter.counter_task_manager.all_tracks_finished',
            args=[well_id]
        )

@shared_task(name="cp_server.tasks_server.tasks.counter.counter_task_manager.all_tracks_finished")
def all_tracks_finished(well_id: str) -> str:
    """
    Runs once when the last track_cells completes for this well_id.
    """
    # 1) Delete the pending counter
    logger.info(f"All tracking done for all FOVs for {well_id}")
    redis_client.delete(f"pending_tracks:{well_id}")  # Clear the pending counter
    
    # 2) Delete all per-FOV hashes
    pattern = f"masks:{well_id}:*"
    for key in redis_client.scan_iter(match=pattern):
        redis_client.delete(key)
        logger.debug(f"Deleted Redis key {key.decode()}")
    
    # 3) Create a finish flag
    finish_key = f"finished:{well_id}"
    redis_client.set(finish_key, 1)
    redis_client.expire(finish_key, 12 * 3600) # Set an expiration time of 12 hours
    
    return f"Run {well_id} completed successfully. All tracks finished."  

@shared_task(name="cp_server.tasks_server.tasks.counter.counter_task_manager.check_and_track")
def check_and_track(hkey: str, track_stitch_threshold: float) -> None:
    """
    Check if there are two masks for the same FOV in Redis. If so, trigger the tracking task.
    Wrapped in try/except to catch Redis errors.
    """
    try:
        # 1) See how many masks we have
        count = redis_client.hlen(hkey)
        logger.debug(f"Redis hlen({hkey}) = {count}")

        if count == 2:
            # 2) Parse well_id and fov_id out of the key name
            _, well_id, fov_id = hkey.split(":", 2)

            # 3) Grab the two mask paths
            raw_vals: List[bytes] = redis_client.hvals(hkey)  # type: ignore
            paths = [p.decode() if isinstance(p, bytes) else str(p) for p in raw_vals]
            logger.info(f"Found 2 masks for {fov_id} in run {well_id}: {paths}")

            # 4) Clean up the hash so we don't double-track
            redis_client.delete(hkey)
            logger.debug(f"Deleted Redis hash {hkey}")

            # 5) Fire off tracking, with a safe callback
            celery_app.send_task(
                'cp_server.tasks_server.tasks.track.track_task.track_cells',
                args=[paths, track_stitch_threshold],
                link=celery_app.signature(
                    'cp_server.tasks_server.tasks.counter.counter_task_manager.mark_one_done',
                    args=[well_id]
                )
            )

    except RedisError as e:
        # Log full stack so you know what happened
        logger.exception(f"Redis error in check_and_track for key {hkey}: {e}")
        # Re-raise if you want Celery to retry this task
        raise

    except Exception as e:
        # Catch anything else unexpected
        logger.exception(f"Unexpected error in check_and_track for key {hkey}: {e}")
        raise    