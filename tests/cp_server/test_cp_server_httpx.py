import subprocess
import time
import httpx

# Start the FastAPI server using uvicorn in a subprocess
server_process = subprocess.Popen(["uvicorn", "cp_server.cp_server_fastapi:app", "--reload"])

# Give the server some time to start
time.sleep(3)

# Define the payload
payload = {"gpu": True,
           "model_type": "cyto3",
           "pretrained_model": False}

# Make a POST request to the /model/ endpoint
response = httpx.post("http://127.0.0.1:8000/model/", json=payload)

# Print the response
print(response.status_code)
print(response.json())

# Terminate the server process
server_process.terminate()