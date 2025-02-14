import os
import json
import base64

import numpy as np
from kombu.serialization import register
from celery import Celery


CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_BACKEND_URL = os.getenv("CELERY_BACKEND_URL", "redis://localhost")


def ndarray_encoder(obj: object) -> str:
    if isinstance(obj, np.ndarray):
        # Convert array to a dict with data encoded in base64 along with metadata
        encoded_data = base64.b64encode(obj.tobytes()).decode('utf-8')
        return json.dumps({
            'data': encoded_data,
            'shape': obj.shape,
            'dtype': str(obj.dtype)})
    raise TypeError('Type not serializable')

def ndarray_decoder(s: str) -> np.ndarray:
    data_dict = json.loads(s)
    data = base64.b64decode(data_dict['data'])
    array = np.frombuffer(data, dtype=data_dict['dtype'])
    return array.reshape(data_dict['shape'])

# Register the custom serializer
register(
    'custom_ndarray',            # Unique name for your serializer
    encoder=ndarray_encoder,  # Your encoder function
    decoder=ndarray_decoder,  # Your decoder function
    content_type='application/x-custom-ndarray',
    content_encoding='utf-8')

def create_celery_app(include_tasks: bool = False)-> Celery:
    app = Celery(
        "cp_server-tasks",
        broker=CELERY_BROKER_URL,
        backend=CELERY_BACKEND_URL,
        broker_connection_retry_on_startup=True)
    
    # Set the custom serializer as the default
    app.conf.update(task_serializer='custom_ndarray',
                    result_serializer='custom_ndarray',
                    accept_content=['application/x-custom-ndarray'])

    # Only load tasks if we're running as a worker
    if include_tasks:
        app.conf.update(include=["cp_server.tasks_server.celery_tasks"],)
    return app


celery_app = create_celery_app(include_tasks=True)
