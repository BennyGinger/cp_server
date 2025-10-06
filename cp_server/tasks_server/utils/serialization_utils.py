import base64
import json
from typing import Any

import numpy as np


class NumpyJSONEncoder(json.JSONEncoder):
    """JSON encoder that knows how to encode NumPy ndarrays.

    The ndarray is converted to a JSON-serialisable dict with a sentinel key
    '__ndarray__' plus dtype, shape and base64 encoded raw bytes.
    """

    def default(self, o: object) -> object:  # type: ignore[override]
        if isinstance(o, np.ndarray):
            encoded_data = base64.b64encode(o.tobytes()).decode('utf-8')
            return {
                '__ndarray__': True,
                'data': encoded_data,
                'shape': o.shape,
                'dtype': str(o.dtype)
            }
        return super().default(o)


def custom_encoder(obj: object) -> str:
    """Encode any Python object (including ndarrays) into a JSON string.

    This is kept as a string because Celery serializer registration expects
    (de)serialisation functions that operate on strings.
    """
    return json.dumps(obj, cls=NumpyJSONEncoder)


def _ndarray_hook(d: dict) -> np.ndarray | dict:
    """Object hook used during JSON loading for ndarray reconstruction."""
    if d.get('__ndarray__'):
        data = base64.b64decode(d['data'])
        array = np.frombuffer(data, dtype=d['dtype'])
        return array.reshape(d['shape'])
    return d


def custom_decoder(s: str | dict[str, Any]) -> object:
    """Decode a JSON string OR already-parsed dict possibly containing ndarrays.

    Accepting both str and dict allows FastAPI endpoints to return the dict form
    (avoiding an extra encode/decode cycle) while Celery still uses the string
    representation.
    """
    if isinstance(s, dict):
        # If this dict itself represents an ndarray, reconstruct directly.
        if s.get('__ndarray__'):
            return _ndarray_hook(s)
        # Otherwise walk shallow values (deep walk not required for current use)
        return {
            k: _ndarray_hook(v) if isinstance(v, dict) else v
            for k, v in s.items()
        }
    return json.loads(s, object_hook=_ndarray_hook)