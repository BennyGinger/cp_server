

class RedisServerError(Exception):
    """Raised when Redis server fails to start."""
    
class CeleryServerError(Exception):
    """Raised when Celery worker fails to start."""
    