import pytest

# Import the classes under test.
from cp_server.fastapi_app.watcher.watcher_manager import FileWatcherManager
from watchdog.events import PatternMatchingEventHandler

###########################
# Dummy Classes for Tests #
###########################

class DummyObserver:
    """A dummy observer to simulate watchdog.observers.Observer"""
    def __init__(self):
        self.scheduled = False
        self.started = False
        self.stopped = False
        self.joined = False

    def schedule(self, event_handler, path, recursive):
        self.scheduled = True
        self.path = path
        self.recursive = recursive

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def join(self):
        self.joined = True

class DummyEventHandler(PatternMatchingEventHandler):
    """A dummy event handler that extends PatternMatchingEventHandler"""
    def __init__(self):
        super().__init__(patterns=["*.tif"], ignore_directories=True, case_sensitive=False)

    def on_created(self, event):
        pass  # No operation for testing purposes

#############################
# Tests for FileWatcherManager
#############################

def test_start_watcher_nonexistent_directory(tmp_path):
    """Ensure that starting a watcher on a non-existent directory raises a ValueError."""
    
    manager = FileWatcherManager()
    non_existent_dir = str(tmp_path.joinpath("nonexistent"))
    with pytest.raises(ValueError):
        manager.start_watcher(non_existent_dir, DummyEventHandler())

def test_start_stop_watcher(tmp_path, monkeypatch):
    """Test that a watcher is started and then stopped properly on a valid directory."""
    # Create a temporary directory.
    valid_dir = tmp_path.joinpath("valid")
    valid_dir.mkdir()

    # Monkeypatch the Observer constructor to return a DummyObserver.
    monkeypatch.setattr(
        "cp_server.fastapi_app.watcher.watcher_manager.Observer",
        lambda: DummyObserver())

    manager = FileWatcherManager()
    handler = DummyEventHandler()
    
    # Start the watcher.
    manager.start_watcher(valid_dir, handler)
    assert valid_dir in manager.observers
    observer = manager.observers[valid_dir]
    assert observer.scheduled, "Observer should have been scheduled."
    assert observer.started, "Observer should have been started."

    # Stop the watcher.
    manager.stop_watcher(valid_dir)
    assert valid_dir not in manager.observers, "Observer should have been removed after stopping."
    assert observer.stopped, "Observer should have been stopped."
    assert observer.joined, "Observer.join() should have been called."

def test_restart_watcher(tmp_path, monkeypatch):
    """Test that starting a watcher on an already-watched directory stops the old one and starts a new one."""
    valid_dir = tmp_path.joinpath("valid")
    valid_dir.mkdir()

    dummy1 = DummyObserver()
    dummy2 = DummyObserver()
    call_count = 0

    def fake_observer():
        nonlocal call_count
        call_count += 1
        return dummy1 if call_count == 1 else dummy2

    monkeypatch.setattr(
        "cp_server.fastapi_app.watcher.watcher_manager.Observer",
        fake_observer)

    manager = FileWatcherManager()
    handler = DummyEventHandler()

    # Start the watcher for the first time.
    manager.start_watcher(valid_dir, handler)
    # Start the watcher a second time for the same directory.
    manager.start_watcher(valid_dir, handler)

    # The first DummyObserver (dummy1) should have been stopped and joined.
    assert dummy1.stopped, "First observer should have been stopped."
    assert dummy1.joined, "First observer should have been joined."
    # The new observer should be dummy2.
    assert manager.observers[valid_dir] is dummy2

def test_stop_watcher_no_watcher():
    manager = FileWatcherManager()
    test_dir = '/tmp/nonexistent_dir'
    with pytest.raises(ValueError, match="No watcher found for this directory"):
        manager.stop_watcher(test_dir)

