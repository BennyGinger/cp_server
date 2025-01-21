import json
import subprocess
import time
import httpx
import atexit

import numpy as np

# Start the FastAPI server using uvicorn in a subprocess
server_process = subprocess.Popen(["uvicorn", "cp_server.cp_server:app", "--reload"])

# Ensure the server process is terminated on exit
atexit.register(server_process.terminate)

# Define a function to check if the server is up
def is_server_up(url, timeout=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = httpx.get(url)
            if response.status_code == 200:
                return True
        except httpx.RequestError:
            time.sleep(0.5)
    return False

# Check if the server is up
server_url = "http://127.0.0.1:8000/health"
if not is_server_up(server_url):
    print("Server did not start in time")
    server_process.terminate()
    exit(1)
    

# Define the payload
payload = {"gpu": True,
           "model_type": "cyto3",
           "pretrained_model": False}

# Make a POST request to the /model/ endpoint
response = httpx.post("http://127.0.0.1:8000/model", json=payload, timeout=180.0)

# Print the response
print(response.status_code)
print(response.json())

# Create a mock image byte array
img_arr = np.random.randint(0, 256, (256, 256), dtype=np.uint8)
img_bytes = img_arr.tobytes()
img_shape = img_arr.shape

# File input
files = {"img_file": ("test_image.png", img_bytes, "image/png")}

response = httpx.post("http://127.0.0.1:8000/segment", 
                      files=files,
                      params={"settings": json.dumps({'diameter':60.,
                                                      'flow_threshold':0.4,
                                                      'cellprob_threshold':0.,}),
                              "target_path": "path/to/save",
                              "img_shape": json.dumps(img_shape)},)

print(response.status_code)
print(response.json()['target_path'])

# Terminate the server process
server_process.terminate()
server_process.wait()