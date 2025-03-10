# CP-Server

Welcome to **CP-Server**, a powerful and efficient FastAPI-based server designed for sending images to be processed in the background via Celery. This server is built to handle image segmentation tasks using the Cellpose library, which is a deep-learning-based model for cell segmentation. The server supports GPU acceleration for faster processing and provides a simple API for interacting with the server. It also includes other features such as background subtraction and simple masks tracking (using iou). The server is also provided with file watchers to automatically detect new images in a folder and process them.

## Features

- **Celery Integration**: Process images in the background using Celery.
- **File Watcher**: Automatically detect new images in a folder and process them.
- **Background Subtraction**: Remove background from images before segmentation.
- **Image Segmentation**: Upload images and receive segmented images as output.
- **Masks Tracking**: Track masks using IOU for simple mask tracking.
- **API Endpoints**: Simple API endpoints for interacting with the server.
- **Model Configuration**: Configure Cellpose model settings via API.
- **GPU Acceleration**: Supports GPU acceleration for faster processing.
- **Health Check**: Endpoint to check server availability.
- **Graceful Shutdown**: Endpoint to gracefully shut down the server.
- **Docker Support**: Provided with Dockerfiles and docker-compose for easy deployment.
- **UV Management**: This project was built using the UV dependency management system, so it contains the uv.lock file which can be used to install the exact dependencies used in the project.
- **Unit Tests**: Contains extensive unit tests for the server, celery tasks and watchers.

## Installation

To install the server, you can use the provided Dockerfiles and docker-compose files to easily deploy the server. You can also install the server manually by following the instructions below.

### Manual Installation

To install the server manually, you need to have Python 3.10 or higher installed on your system. You can then install the required dependencies using the following command:

```bash
pip install -r pyproject.toml
```

## API Endpoints

The server provides the following API endpoints for interacting with the server:

- **GET /health**: Check the health of the server.
- **POST /segment**: Upload a folder of images to be segmented. The masks will be saved in the output folder.
- **POST /start-segment-watcher**: Start the file watcher to detect new images in the input folder and process them.
- **POST /start-tracking-watcher**: Start the file watcher to detect new masks in the masks folder and track them.
- **POST /stop-dir-watcher**: Stop the file watcher for the given directory.

## Authors

- Benoit Roux - [benoit.roux@gmail.com](mailto:benoit.roux@gmail.com)
- Raphael Feurstein - [raphael.feurstein@gmail.com](mailto:raphael.feurstein@gmail.com)

## License

This project is licensed under the MIT License.