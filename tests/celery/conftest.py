import pytest
from cp_server.tasks_server.celery_app import celery_app


@pytest.fixture(scope="session", autouse=True)
def configure_celery_for_tests():
    celery_app.conf.task_always_eager = True
    celery_app.conf.result_backend = 'cache'
