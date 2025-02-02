import subprocess
import time

import httpx


def start_server()-> subprocess.Popen:
    server_process = subprocess.Popen(["uvicorn", "cp_server.main:app"])
    return server_process

def is_server_up(timeout: int=10)-> bool:
    """Define a function to check if the server is up"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = httpx.get("http://127.0.0.1:8000/")
            if response.status_code == 200:
                return True
        except httpx.RequestError:
            time.sleep(0.5)
    return False

def check_mount_dirs(src_dir: str, dst_dir: str)-> None:
    """Define a function to check the mount directories"""
    try:
        response = httpx.post("http://127.0.0.1:8000/mount", json={"src_dir": src_dir, "dst_dir": dst_dir})
    
        print(f"Dirs were mounted: {response.json()}")
    
    except httpx.RequestError as e:
        print(f"An error occurred: {e}")
    except httpx.HTTPStatusError as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

def stop_servers()-> None:
    """Define a function to stop the server"""
    try:
        response = httpx.post("http://127.0.0.1:8000/stop")
        print(f"Server was stopped: {response.json()}")
    except httpx.RequestError as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

def main(payload: dict)-> None:
    try:
        server = start_server()
        if not is_server_up():
            raise RuntimeError("Server did not start in time")
        
        print("Server is up!")
        
        check_mount_dirs(payload["src_dir"], payload["dst_dir"])
    
    except RuntimeError as r:
        print(f"Server did not start in time {r}")
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        stop_servers()
        server.terminate()
        server.wait()
        
if __name__ == "__main__":
    payload = {"src_dir": "/home/ben/Lab/Python/cp_server/Image_tests/Images",
                "dst_dir": "/home/ben/Lab/Python/cp_server/Image_tests"}
    
    main(payload)