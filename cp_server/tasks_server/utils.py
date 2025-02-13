import io
import base64

import numpy as np


def ndarray_to_bytes(arr: np.ndarray) -> bytes:
    buffer = io.BytesIO()
    np.save(buffer, arr)
    return buffer.getvalue()

def bytes_to_ndarray(b: bytes) -> np.ndarray:
    buffer = io.BytesIO(b)
    buffer.seek(0)  # Ensure the pointer is at the start
    return np.load(buffer)

def encode_ndarray_as_bytesb64(arr: np.ndarray) -> str:
    arr_bytes = ndarray_to_bytes(arr)
    return base64.b64encode(arr_bytes).decode('utf-8')

def decode_bytesb64_to_array(b64_str: str) -> np.ndarray:
    arr_bytes = base64.b64decode(b64_str.encode('utf-8'))
    return bytes_to_ndarray(arr_bytes)
