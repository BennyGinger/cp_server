import pytest
import importlib.util

if importlib.util.find_spec("celery") is None:
    pytest.skip("celery not installed", allow_module_level=True)
else:
    from cp_server.tasks_server.celery_app import celery_app


@pytest.fixture(scope="session", autouse=True)
def configure_celery_for_tests():
    celery_app.conf.task_always_eager = True
    celery_app.conf.result_backend = 'cache'
