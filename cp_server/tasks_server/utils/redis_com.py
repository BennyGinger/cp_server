# Initialize Redis client from CELERY_BROKER_URL environment variable
import os
from urllib.parse import urlparse

from redis import Redis


url = os.environ["CELERY_BROKER_URL"]  # e.g. redis://redis:6379/2
parse_url = urlparse(url)
redis_client = Redis(host=parse_url.hostname or "localhost", 
                     port=parse_url.port or 6379, 
                     db=int(parse_url.path.lstrip("/")) if parse_url.path else 2)