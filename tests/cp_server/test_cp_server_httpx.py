import base64
import json
from pathlib import Path
import subprocess
import time
import httpx
import numpy as np
import tifffile


def start_server()-> subprocess.Popen:
    server_process = subprocess.Popen(["uvicorn", "cp_server.cp_server:app", "--timeout-keep-alive", "180"])
    return server_process

def is_server_up(timeout: int=10)-> bool:
    """Define a function to check if the server is up"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = httpx.get("http://127.0.0.1:8000/health")
            if response.status_code == 200:
                return True
        except httpx.RequestError:
            time.sleep(0.5)
    return False

def check_model_creation(payload: dict)-> dict:
    response = httpx.post("http://127.0.0.1:8000/model", json=payload, timeout=180.0)

    print(f"Model was created with response {response.status_code} and output {response.json()}")
    return response.json()

def check_image_segmentation(settings: dict, img: Path | np.ndarray, target_path: str)-> dict:
    # File input
    if isinstance(img, np.ndarray):
        img_arr = img
        files = {"img_file": ("test_image.png", img_arr.tobytes(), "image/png")}
    
    elif isinstance(img, Path):
        img_arr = tifffile.imread(img)
        if img_arr.ndim > 3:
            img_arr = img_arr[0]
        files = {"img_file": (img.name, img_arr.tobytes(), f"image/{img.suffix}")}
    
    # Pack the data
    data = {"settings": json.dumps(settings),
            "target_path": target_path,
            "img_shape": json.dumps(img_arr.shape)}
    # data = {"settings": settings,
    #         "target_path": target_path,
    #         "img_shape": img_arr.shape}
    
    response = httpx.post("http://127.0.0.1:8000/segment",
                            files=files,
                            params=data)
    
    print(f"Image was segmented with response {response.status_code} and output {response.json().keys()}")
    return response.json()


def main(payload: dict, settings: dict, img: Path, target_path: str)-> dict:
    try:
        server = start_server()
        if not is_server_up():
            raise RuntimeError("Server did not start in time")
        
        print("Server is up!")
        
        resp = check_model_creation(payload)
        resp = check_image_segmentation(settings, img, target_path)

        return resp
    
    except RuntimeError as r:
        print(f"Server did not start in time {r}")
    
    except ValueError as v:
        print(f"Invalid model type: {v}")
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        server.terminate()
        server.wait()


if __name__ == "__main__":
    
    # Define the payload
    payload = {"gpu": True,
               "model_type": "cyto3",
               "pretrained_model": False}
    
    # img_arr = np.random.randint(0, 256, (256, 256), dtype=np.uint8)
    img_path = Path("/media/ben/Analysis/Python/cp_server/Image_tests/z_stack.tif")
    
    settings = {'diameter':60.,'flow_threshold':0.4,'cellprob_threshold':0.,'stitch_threshold':0.8}
    
    target_path = "/media/ben/Analysis/Python/cp_server/Image_tests/server_mask_z_stack.tif"
    # target_path = "path/to/target"
    
    resp = main(payload, settings, img_path, target_path)
    
    print(resp.keys())
    mask_base64 = resp["mask"]
    mask_bytes = base64.b64decode(mask_base64)
    mask_arr = np.frombuffer(mask_bytes, dtype=np.uint16).reshape((25,1024, 1024))
    tifffile.imwrite(resp["target_path"], mask_arr)
    print("All tests passed!")