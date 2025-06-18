import pytest
import importlib.util

if importlib.util.find_spec("fastapi") is None:
    pytest.skip("fastapi not installed", allow_module_level=True)
