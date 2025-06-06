# Initialize Redis client from CELERY_BROKER_URL environment variable
import os
from urllib.parse import urlparse

from redis import Redis, RedisError


url = os.environ["CELERY_BROKER_URL"]  # e.g. redis://redis:6379/0
parse_url = urlparse(url)
redis_client = Redis(host=parse_url.hostname, port=parse_url.port, db=int(parse_url.path.lstrip("/")))