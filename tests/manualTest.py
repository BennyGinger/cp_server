import httpx


def check_segment(payload: dict)-> None:
    """Test the segment endpoint"""
    try:
        response = httpx.post("http://0.0.0.0:8000/segment", json=payload)
        print(f"Segment response: {response.json()}")
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


        
if __name__ == "__main__":
    payload = {"src_folder": "Images",
               "directory": "/app/data",
               "settings": {"model": {"model_type": "cyto3",
                                      "restore_type": "denoise_cyto3",
                                      "gpu": True},
                            "segmentation": {"diameter": 60,
                                             "flow_threshold": 0.4,
                                             "cellprob_threshold": 0.0,
                                             "do_3D": True,}},
               "dst_folder": "/app/data/Masks_CP",
               "key_label": "_z",
               "do_denoise": True}
    
    check_segment(payload)