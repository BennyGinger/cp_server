import base64
import json

import numpy as np


class NumpyJSONEncoder(json.JSONEncoder):
    def default(self, o: object) -> object:
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
    # Use the custom encoder for the entire payload.
    return json.dumps(obj, cls=NumpyJSONEncoder)

def custom_decoder(s: str) -> object:
    def hook(d: dict)-> np.ndarray | dict:
        if d.get('__ndarray__'):
            data = base64.b64decode(d['data'])
            array = np.frombuffer(data, dtype=d['dtype'])
            return array.reshape(d['shape'])
        return d
    return json.loads(s, object_hook=hook)