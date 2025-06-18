import pytest
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from cp_server.fastapi_app.main import app
from cp_server.fastapi_app.endpoints import process_tasks

class DummyResult:
    def __init__(self, id="dummy"):
        self.id = id

class DummyCelery:
    def __init__(self):
        self.calls = []
    def send_task(self, name, kwargs):
        self.calls.append((name, kwargs))
        return DummyResult()

class DummyRedis:
    def __init__(self):
        self.store = {}
    def setnx(self, key, val):
        if key not in self.store:
            self.store[key] = val
    def expire(self, key, secs):
        pass
    def exists(self, key):
        return key in self.store
    def get(self, key):
        return self.store.get(key)
    def delete(self, key):
        self.store.pop(key, None)

def setup_app(dummy_celery, monkeypatch):
    app.state.celery_app = dummy_celery
    monkeypatch.setattr(process_tasks, "redis_client", DummyRedis())
    return TestClient(app)


def make_payload(tmp_path):
    img_file = tmp_path / "A1_test_1.tif"
    img_file.write_text("x")
    dst = tmp_path / "out"
    payload = {
        "img_path": str(img_file),
        "sigma": 0.0,
        "size": 7,
        "cellpose_settings": {},
        "dst_folder": str(dst),
        "run_id": "run1",
        "total_fovs": 1,
    }
    return payload


def test_process_images(monkeypatch, tmp_path):
    dummy_celery = DummyCelery()
    client = setup_app(dummy_celery, monkeypatch)
    payload = make_payload(tmp_path)

    resp = client.post("/process", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"run_id": "run1", "task_ids": "dummy"}

    assert dummy_celery.calls
    name, kwargs = dummy_celery.calls[0]
    assert name == "cp_server.tasks_server.tasks.celery_main_task.process_images"
    assert kwargs["img_path"] == payload["img_path"]
    assert kwargs["dst_folder"] == payload["dst_folder"]


def test_process_bg_sub(monkeypatch, tmp_path):
    dummy_celery = DummyCelery()
    client = setup_app(dummy_celery, monkeypatch)
    img = tmp_path / "im.tif"
    img.write_text("x")
    payload = {"img_path": str(img), "sigma": 0.0, "size": 7}

    resp = client.post("/process_bg_sub", json=payload)
    assert resp.status_code == 200
    assert resp.json() == "dummy"
    assert dummy_celery.calls
    name, kwargs = dummy_celery.calls[0]
    assert name == "cp_server.tasks_server.tasks.bg_sub.remove_bg"
    assert kwargs["img_path"] == payload["img_path"]


def test_process_status(monkeypatch):
    dummy_celery = DummyCelery()
    redis = DummyRedis()
    monkeypatch.setattr(process_tasks, "redis_client", redis)
    client = TestClient(app)
    app.state.celery_app = dummy_celery

    redis.setnx("pending_tracks:run1", 2)
    resp = client.get("/process/run1/status")
    assert resp.status_code == 200
    assert resp.json() == {"run_id": "run1", "status": "processing", "remaining": 2}

    redis.delete("pending_tracks:run1")
    redis.setnx("finished:run1", True)
    resp = client.get("/process/run1/status")
    assert resp.status_code == 200
    assert resp.json() == {"run_id": "run1", "status": "finished", "remaining": 0}

    redis.delete("finished:run1")
    resp = client.get("/process/run1/status")
    assert resp.status_code == 404

