from typing import Optional, List, Union

from celery import shared_task

from cp_server.tasks_server import get_logger
from cp_server.tasks_server.utils.redis_com import redis_client
from cp_server.tasks_server.celery_app import celery_app
from redis import RedisError


logger = get_logger('counter_tasks')

@shared_task(name="cp_server.tasks_server.tasks.counter.counter_task_manager.mark_one_done")
def mark_one_done(track_result, well_id: str) -> Optional[str]:
    """
    Celery callback: decrement the pending counter; if zero, fire final task.
    The track_result parameter receives the return value from the track_cells task.
    """
    # Log the track result (optional, can be removed if not needed)
    logger.debug(f"Track task completed with result: {track_result}")
    
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
def check_and_track(hkey: Union[str, List[str]], track_stitch_threshold: float) -> None:
    """
    Check if there are two masks for the same FOV in Redis. If so, trigger the tracking task.
    Can process a single hkey or a list of hkeys for batch operation.
    Wrapped in try/except to catch Redis errors.
    """
    def process_single_key(single_hkey: str):
        try:
            # 1) See how many masks we have
            count = redis_client.hlen(single_hkey)
            logger.debug(f"Redis hlen({single_hkey}) = {count}")

            if count == 2:
                # 2) Parse well_id and fov_id out of the key name
                _, well_id, fov_id = single_hkey.split(":", 2)

                # 3) Grab the two mask paths
                raw_vals: List[bytes] = redis_client.hvals(single_hkey)  # type: ignore
                paths = [p.decode() if isinstance(p, bytes) else str(p) for p in raw_vals]
                logger.info(f"Found 2 masks for {fov_id} in run {well_id}: {paths}")

                # 4) Clean up the hash so we don't double-track
                redis_client.delete(single_hkey)
                logger.debug(f"Deleted Redis hash {single_hkey}")

                # 5) Fire off tracking, with a safe callback
                celery_app.send_task(
                    'cp_server.tasks_server.tasks.track.track_cells',
                    args=[paths, track_stitch_threshold],
                    link=celery_app.signature(
                        'cp_server.tasks_server.tasks.counter.counter_task_manager.mark_one_done',
                        args=[well_id]))

        except RedisError as e:
            logger.exception(f"Redis error in check_and_track for key {single_hkey}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in check_and_track for key {single_hkey}: {e}")
            raise

    if isinstance(hkey, list):
        logger.info(f"Batch check_and_track for {len(hkey)} keys.")
        for single_hkey in hkey:
            process_single_key(single_hkey)
    else:
        process_single_key(hkey)