import logging
import warnings
from fastapi import FastAPI
from cp_server.endpoints import health, shutdown, model, segment


# Suppress FutureWarning messages from cellpose
warnings.filterwarnings("ignore", category=FutureWarning, module="cellpose")

# Default cellpose settings
MODEL_SETTINGS = {'gpu':True,
                  'model_type': 'cyto2',
                  'pretrained_model':False}


# Initialize FastAPI app
app = FastAPI()

# Register routers
app.include_router(health.router)
app.include_router(model.router)
app.include_router(shutdown.router)
app.include_router(segment.router)

# Log model creation
logging.info("The app is ready to accept requests")


if __name__ == "__main__":
    import httpx

    # Define the payload
    payload = {
        "gpu": True,
        "model_type": "cyto3",
        "pretrained_model": False
    }

    # Make a POST request to the /model/ endpoint
    response = httpx.post("http://127.0.0.1:8000/model/", json=payload)

    # Print the response
    print(response.status_code)
    print(response.json())