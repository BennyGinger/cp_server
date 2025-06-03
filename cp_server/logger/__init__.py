import logging
import os
import json
import redis


SERVICE_NAME = os.getenv("SERVICE_NAME", "cp_server")

class RedisLogHandler(logging.Handler):
    """
    A logging.Handler that serializes each LogRecord to JSON
    and LPUSHes it into a Redis list.
    """

    def __init__(self,
                 host: str = None,
                 port: int = None,
                 db: int = None,
                 queue_name: str = None):
        super().__init__()

        self.redis_host  = host or os.getenv("REDIS_HOST", "redis")
        self.redis_port  = port or int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db    = db   or int(os.getenv("REDIS_DB", "2"))
        self.queue_name  = queue_name or os.getenv("LOG_QUEUE_NAME", "log_queue")

        # Make a Redis client—this is where logs will be pushed:
        self._client = None  # type: redis.Redis

    def _get_redis_client(self):
        """
        Lazily create and return a Redis client. If connection fails,
        return None (so emit can skip).
        """
        if self._client is None:
            try:
                client = redis.Redis(
                    host=self.redis_host,
                    port=self.redis_port,
                    db=self.redis_db,
                    decode_responses=False,  # we push raw bytes
                )
                # Try a quick ping to see if Redis is reachable.
                client.ping()
                self._client = client
            except redis.exceptions.ConnectionError:
                # Redis is not available right now. Don’t set self._client
                # so future emits can retry.
                self._client = None
        return self._client
    
    def emit(self, record: logging.LogRecord):
        try:
            # Determine timestamp using the handler's formatter if available, otherwise fall back to formatting record.created manually.
            if hasattr(self, "formatter") and self.formatter:
                datefmt = getattr(self.formatter, "datefmt", None)
                asctime = self.formatter.formatTime(record, datefmt=datefmt)
            else:
                asctime = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
            
            payload = {
                "name":     record.name,
                "level":    record.levelname,
                "message":  record.getMessage(),
                "asctime":  asctime,
                "pathname": record.pathname,
                "lineno":   record.lineno,
                "funcName": record.funcName,
                "process":  record.process,
                "thread":   record.threadName,
            }
            json_payload = json.dumps(payload).encode("utf-8")
            
            client = self._get_redis_client()
            if client is None:
                # Could not connect to Redis; drop this log silently.
                return
            # Push onto Redis list. If this raises ConnectionError, it will jump to except below.
            client.lpush(self.queue_name, json_payload)
        
        except redis.exceptions.ConnectionError:
            # If Redis goes down after we fetched a client, drop the log.
            return
        
        except Exception as e:
            # For any other errors (e.g. JSON encoding), fallback to default handlerError logging:
            self.handleError(record)

def _setup_logging() -> None:
    """
    Set up the root logger to use RedisLogHandler.
    This function configures the logging level based on the LOG_LEVEL environment variable,
    and attaches a RedisLogHandler to the root logger.
    If the LOG_LEVEL is not set, it defaults to INFO.
    If the RedisLogHandler is already attached, it does nothing.
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    root_level = getattr(logging, level_name, logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(root_level)

    # Avoid double‐attaching if startup() is called twice:
    already = [type(h) for h in root_logger.handlers]
    if RedisLogHandler not in already:
        redis_handler = RedisLogHandler()
        fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        redis_formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
        redis_handler.setFormatter(redis_formatter)
        root_logger.addHandler(redis_handler)

def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger with the specified name, or the root logger if no name is provided.
    The logger will be configured to use RedisLogHandler.
    """
    _setup_logging()  # Ensure logging is set up before returning the logger
    base = SERVICE_NAME
    return logging.getLogger(f"{base}.{name}") if name else logging.getLogger(base)
    


