# cp_server/logging.py
import os
import logging

SERVICE_NAME = os.getenv("SERVICE_NAME", "cp_server")

def get_logger(name: str = None) -> logging.Logger:
    base = SERVICE_NAME
    return logging.getLogger(f"{base}.{name}") if name else logging.getLogger(base)


# TODO: Use the following code to set up logging in your application.
# from pathlib import Path
# import logging
# from logging.handlers import RotatingFileHandler
# from celery.signals import after_setup_logger, after_setup_task_logger
# from cp_server.logging import SERVICE_NAME

# # 1) Prepare your log directory
# log_dir = Path("/var/log") / "a1_pipeline"
# log_dir.mkdir(parents=True, exist_ok=True)

# # 2) Common formatter & console handler
# fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
# datefmt = "%Y-%m-%d %H:%M:%S"
# formatter = logging.Formatter(fmt, datefmt=datefmt)

# ch = logging.StreamHandler()
# ch.setLevel(logging.INFO)
# ch.setFormatter(formatter)
# logging.getLogger().addHandler(ch)
# logging.getLogger().setLevel(logging.DEBUG)

# # 3) File handlers for cp_server and cp_server.celery
# fh_main = RotatingFileHandler(
#     filename=log_dir / f"{SERVICE_NAME}.log",
#     maxBytes=10_000_000, backupCount=5, encoding="utf-8"
# )
# fh_main.setLevel(logging.DEBUG)
# fh_main.setFormatter(formatter)
# logging.getLogger(SERVICE_NAME).addHandler(fh_main)

# fh_cel = RotatingFileHandler(
#     filename=log_dir / f"{SERVICE_NAME}_celery.log",
#     maxBytes=5_000_000, backupCount=3, encoding="utf-8"
# )
# fh_cel.setLevel(logging.DEBUG)
# fh_cel.setFormatter(formatter)
# logging.getLogger(f"{SERVICE_NAME}.celery").addHandler(fh_cel)

# # 4) Re-apply after Celery starts
# @after_setup_logger.connect
# @after_setup_task_logger.connect
# def _reconfig_celery(logger, *args, **kwargs):
#     # Redis is just the broker; log records still flow over Python logging.
#     # This hook makes sure your handlers get wired *after* Celery hijacks the root.
#     logging.getLogger().handlers = logging.getLogger().handlers  # no-op, handlers are already in place
#     # if you wanted to adjust levels/filters post-startup, you could do it here
