from pathlib import Path
import types
import sys
import pytest

# Avoid executing cp_server/__init__ which requires a .env file
pkg_root = Path(__file__).resolve().parents[1] / "cp_server"
if "cp_server" not in sys.modules:
    stub = types.ModuleType("cp_server")
    stub.__path__ = [str(pkg_root)]
    sys.modules["cp_server"] = stub

# Provide a minimal stub for cp_server.tasks_server to avoid Celery dependency
ts_root = pkg_root / "tasks_server"
tasks_stub = types.ModuleType("cp_server.tasks_server")
tasks_stub.__path__ = [str(ts_root)]
import logging
tasks_stub.get_logger = lambda name=None: logging.getLogger(name or "tasks_server")
sys.modules.setdefault("cp_server.tasks_server", tasks_stub)

celery_stub = types.ModuleType("cp_server.tasks_server.celery_app")
def create_celery_app(include_tasks: bool = False):
    class Dummy:
        def send_task(self, *a, **k):
            return type("R", (), {"id": "dummy"})()
    return Dummy()
celery_stub.create_celery_app = create_celery_app
celery_stub.celery_app = create_celery_app()
sys.modules.setdefault("cp_server.tasks_server.celery_app", celery_stub)


@pytest.fixture
def temp_dir(tmp_path)-> Path:
    # Create temp dir structure
    temp_dir = tmp_path.joinpath("level1", "level2")
    temp_dir.mkdir(parents=True)
    return temp_dir

@pytest.fixture
def create_file(temp_dir: Path):
    def _create_file(filename: str)-> Path:
        img_file = temp_dir.joinpath(filename)
        img_file.touch()
        return img_file
    return _create_file

@pytest.fixture
def img():
    np = pytest.importorskip("numpy")
    return np.random.randint(0, 65536, (256, 256), dtype=np.uint16)

@pytest.fixture
def img_zstack():
    np = pytest.importorskip("numpy")
    return np.random.randint(0, 65536, (10, 256, 256), dtype=np.uint16)

@pytest.fixture
def payload():
    return {
        "settings": {"example": {"option": "value"}},
        "dst_folder": "dst",
        "key_label": "test",
        "do_denoise": False,}

@pytest.fixture
def track_payload():
    return {
        "directory": "/tmp/watch",
        "stitch_threshold": 0.1,}

class DummyCelery:
    """A simple dummy celery app that records task submissions."""
    def __init__(self):
        self.tasks = []

    def send_task(self, name, kwargs):
        self.tasks.append((name, kwargs))

@pytest.fixture
def fake_celery():
    return DummyCelery()

class FakeWatcherManager:
    def __init__(self):
        self.celery_app = DummyCelery()

@pytest.fixture
def fake_manager():
    return FakeWatcherManager()
