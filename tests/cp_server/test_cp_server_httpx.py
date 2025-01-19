import subprocess
import time
import httpx
import atexit

# Start the FastAPI server using uvicorn in a subprocess
server_process = subprocess.Popen(["uvicorn", "cp_server.cp_server_fastapi:app", "--reload"])

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
response = httpx.post("http://127.0.0.1:8000/model/", json=payload)

# Print the response
print(response.status_code)
print(response.json())

# Terminate the server process
server_process.terminate()
server_process.wait()