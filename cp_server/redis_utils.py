import subprocess
import time
import redis
import os
from pathlib import Path
import sys

# Resolve the root of the project dynamically
ROOT_DIR = Path(__file__).resolve().parent.parent

# Add root directory to sys.path if it's not already there
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from cp_server import logger  # noqa: E402


# Configurable Redis settings
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PROCESS = None

def is_redis_running():
    """Check if Redis server is running."""
    try:
        client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        return client.ping()  # Returns True if Redis is running
    except redis.ConnectionError:
        return False

def start_redis():
    """Start Redis server if it's not already running, with a timeout."""
    global REDIS_PROCESS
    if not is_redis_running():
        logger.info("Starting Redis server...")
        
        # Run Redis as a subprocess
        REDIS_PROCESS = subprocess.Popen(
            ["redis-server"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for Redis to start (max 2 minutes)
        timeout = 120
        interval = 2
        elapsed_time = 0

        while not is_redis_running() and elapsed_time < timeout:
            time.sleep(interval)
            elapsed_time += interval
            logger.info(f"Waiting for Redis to start... {elapsed_time}s elapsed")

        if is_redis_running():
            logger.info("Redis server started successfully.")
        else:
            logger.error("Redis server did not start within the timeout period.")
            REDIS_PROCESS.terminate()  # Kill Redis if it fails to start
    else:
        logger.info("Redis is already running.")

def stop_redis():
    """Stop Redis server if it was started as a subprocess."""
    global REDIS_PROCESS
    if REDIS_PROCESS:
        logger.info("Stopping Redis server...")
        REDIS_PROCESS.terminate()  # Sends SIGTERM
        REDIS_PROCESS.wait()  # Wait for it to exit
        REDIS_PROCESS = None
        logger.info("Redis server stopped.")
    else:
        logger.warning("No Redis process tracked. Trying shutdown command.")
        try:
            client = redis.Redis(host="localhost", port=6379)
            client.shutdown()
            logger.info("Redis shut down via shutdown command.")
        except redis.ConnectionError:
            logger.error("Redis is not running or unreachable.")
        except redis.exceptions.ResponseError:
            logger.error("Redis shutdown failed. It may require authentication.")
            
            
if __name__ == "__main__":
    # start_redis()
    # print(is_redis_running())
    stop_redis()
    print(is_redis_running())
    time.sleep(5)
    print(is_redis_running())