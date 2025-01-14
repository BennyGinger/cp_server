"""
Cellpose Segmentation Server

This script sets up a Flask server that listens for incoming image data, processes the images using the Cellpose model for cell segmentation, and returns the segmentation masks.
The server supports both .tif and other common image formats (e.g., .jpg, .png) as input, and always returns the segmentation masks in .tif format.

The server checks for the presence of a compatible NVIDIA GPU at startup. If a GPU is available, the Cellpose model is initialized with GPU support; otherwise, it falls back to CPU to avoid errors on machines without a GPU.

To run the server:
    python cellpose_server.py

Endpoints:
    /segment (POST): Accepts an image file, processes it using Cellpose, and returns the segmentation mask in .tif format along with the target path.
    /update_model (POST): Updates the Cellpose model settings.
    /shutdown (POST): Shuts down the server gracefully.

Request Payload for /segment:
    The request should be a JSON object with the following fields:
    - image: Base64-encoded string of the image file.
    - file_extension: (Optional) The file extension of the image (e.g., '.tif'). Defaults to '.tif'.
    - target_path: Path where the processed image should be saved.

Response for /segment:
    The response is a JSON object with the following field:
    - mask: Base64-encoded string of the segmentation mask in .tif format.
    - target_path: Path where the processed image should be saved.

Request Payload for /update_model:
    The request should be a JSON object with the following fields:
    - model_type: (Optional) The type of Cellpose model to use (e.g., 'cyto'). Defaults to 'cyto'.
    - gpu: (Optional) Boolean indicating whether to use GPU. Defaults to True.
    - diameter: (Optional) Diameter of the cells to be segmented. Defaults to 40.
    - flow_threshold: (Optional) Flow threshold for the Cellpose model. Defaults to 1.
    - cellprob_threshold: (Optional) Cell probability threshold for the Cellpose model. Defaults to 0.
    - Any other Cellpose settings as needed.

Response for /update_model:
    The response is a JSON object with the following field:
    - status: Status of the update operation.
    - message: Additional information about the update operation.

=== Example Client-Side Request for /segment: ===
    import requests
    import base64

    def send_image_to_server(image_path, file_extension):
        with open(image_path, 'rb') as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')

        payload = {
            'image': image_data,
            'file_extension': file_extension
            'target_path': 'path/to/save'
        }

        response = requests.post('http://localhost:5000/segment', json=payload)
        result = response.json()

        # Decode the mask data
        mask_data = base64.b64decode(result['mask'])

        # Save the processed image to the target path
    with open(result['target_path'], 'wb') as f:
        f.write(mask_data)

    # Example usage
    send_image_to_server('path/to/image.jpg', '.jpg')

=== Example Client-Side Request for /update_model: ===
    import requests

    def update_model_settings():
        payload = {
            "model_type": "cyto",
            "gpu": True,
            "flow_threshold": 4,
            "diameter": 30,
            "cellprob_threshold": 0.5
        }

        response = requests.post("http://localhost:5000/update_model", json=payload)
        return response.json()

=== Example Client-Side Request for /shutdown: ===
    import requests

    def shutdown_server():
        response = requests.post('http://localhost:5000/shutdown')
        print(response.text)

    # Example usage
    shutdown_server()

=== Example Client-Side Check for Server Availability: ===
    import socket

    def is_server_available(host, port):
        try:
            with socket.create_connection((host, port), timeout=5):
                return True
        except (OSError, socket.timeout):
            return False

    # Example usage
    host = 'localhost'
    port = 5000
    if is_server_available(host, port):
        print(f"Server is available at {host}:{port}")
    else:
        print(f"Server is not available at {host}:{port}")

Notes:
- Ensure that the server is running on a machine with a compatible NVIDIA GPU if GPU support is enabled.
- The server uses the Cellpose model with GPU support for faster processing if a GPU is available.
- The client-side script should handle the base64 encoding and decoding of image data.
- The server handles graceful shutdown by capturing SIGINT and SIGTERM signals and performing cleanup operations.
"""

import atexit
import base64
import io
import logging
import signal
from pathlib import Path

import cv2
import numpy as np
import tifffile as tiff
from cellpose import core, models
from flask import Flask, jsonify, request

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Check for GPU availability
GPU_AVAILABLE = core.use_gpu()
if GPU_AVAILABLE:
    print("This is the Cellpose server running with GPU")
else:
    print("No NVIDIA GPU found. Running on CPU.")

# default model_type
DEFAULT_MODEL_TYPE = "cyto"

# Initialize Cellpose model with GPU support if available
try:
    model = models.Cellpose(gpu=GPU_AVAILABLE, model_type=DEFAULT_MODEL_TYPE)
except AttributeError as e:
    print(f"Error initializing Cellpose model: {e}")
    model = models.Cellpose(gpu=False, model_type=DEFAULT_MODEL_TYPE)

# Global dictionary to store additional parameters
model_params = {"diameter": 40, "flow_threshold": 1, "cellprob_threshold": 0}


def decode_image(image_data, file_extension):
    image_io = io.BytesIO(image_data)
    if file_extension.lower() == "tif" or file_extension.lower() == "tiff":
        img = tiff.imread(image_io)
    else:
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


@app.route("/segment", methods=["POST"])
def segment():
    """
    Endpoint to process an image and return the segmentation mask along with the target path.

    Expects a JSON payload with the following fields:
    - image: Base64 encoded image data
    - file_extension: (Optional) File extension of the image, defaults to '.tif'
    - target_path: Path where the processed image should be saved

    Returns a JSON response with the following fields:
    - mask: Base64 encoded segmentation mask
    - target_path: Path where the processed image should be saved
    """
    try:
        data = request.json
        image_data = base64.b64decode(data["image"])
        file_extension = data.get("file_extension", ".tif")  # default to tif
        target_path = Path(data["target_path"])

        img = decode_image(image_data, file_extension)

        # Use the stored parameters in model_params for the eval function
        masks, _, _, _ = model.eval(img, **model_params)

        mask_io = io.BytesIO()
        tiff.imwrite(mask_io, masks)
        mask_str = base64.b64encode(mask_io.getvalue()).decode("utf-8")

        return jsonify({"mask": mask_str, "target_path": str(target_path)}), 200
    except Exception as e:
        logging.error(f"Error processing image: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/update_model", methods=["POST"])
def update_model():
    """
    Endpoint to update the Cellpose model settings.
    """
    try:
        data = request.json
        model_type = data.get("model_type", "cyto")
        gpu_requested = data.get("gpu", True)
        gpu = gpu_requested and GPU_AVAILABLE

        # Extract additional settings for Cellpose
        additional_settings = {
            key: value
            for key, value in data.items()
            if key not in ["model_type", "gpu"]
        }

        # Update the model with new settings
        global model
        model = models.Cellpose(gpu=gpu, model_type=model_type)

        # Update global model_params with additional settings
        global model_params
        model_params.update(additional_settings)

        if gpu_requested and not GPU_AVAILABLE:
            return jsonify(
                {
                    "status": "warning",
                    "message": "GPU requested but not available. Model initialized with CPU instead of GPU.",
                }
            ), 200

        return "", 200
    except Exception as e:
        logging.error(f"Error updating model: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/shutdown", methods=["POST"])
def shutdown():
    """
    Endpoint to shut down the server gracefully.
    """
    shutdown_server()
    return "Server shutting down...", 200


def shutdown_server():
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()


def cleanup():
    print("Server shutting down...")
    model = None
    print("Cellpose model released")


def handle_signal(signal, frame):
    cleanup()
    exit(0)


def start_server():
    host = "0.0.0.0"
    port = 5000
    print(f"Cellpose server started on {host}:{port}")
    app.run(host=host, port=port)


if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Register cleanup function for cleanup on exit
    atexit.register(cleanup)

    start_server()
