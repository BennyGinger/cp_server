from pathlib import Path
import numpy as np
import pytest


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
    return np.random.randint(0, 65536, (256, 256), dtype=np.uint16)

@pytest.fixture
def img_zstack():
    return np.random.randint(0, 65536, (10, 256, 256), dtype=np.uint16)

@pytest.fixture
def payload():
    return {
        "settings": {"example": {"option": "value"}},
        "dst_folder": "dst",
        "key_label": "test",
        "do_denoise": False,}

# A simple dummy celery app that records task submissions.
class DummyCelery:
    def __init__(self):
        self.tasks = []

    def send_task(self, name, kwargs):
        self.tasks.append((name, kwargs))

class FakeWatcherManager:
    def __init__(self):
        self.celery_app = DummyCelery()

@pytest.fixture
def fake_celery():
    return DummyCelery()

@pytest.fixture
def fake_manager():
    return FakeWatcherManager()