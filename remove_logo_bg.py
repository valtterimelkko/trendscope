#!/usr/bin/env python3
"""
Remove background from logo using Runware API
"""

import requests
import os
from uuid import uuid4

API_KEY = os.environ.get("RUNWARE_API_KEY")
API_URL = "https://api.runware.ai/v1"

def remove_background(input_image_path, output_path):
    """Remove background from image using Runware API"""
    
    # Read image and convert to base64
    import base64
    with open(input_image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    
    task_uuid = str(uuid4())
    
    payload = [
        {
            "taskType": "removeBackground",
            "taskUUID": task_uuid,
            "inputImage": f"data:image/png;base64,{image_data}",
            "outputType": "URL",
            "outputFormat": "PNG",
            "model": "runware:109@1",  # RemBG 1.4
            "settings": {
                "rgba": [255, 255, 255, 0],
                "postProcessMask": True,
                "returnOnlyMask": False,
                "alphaMatting": True,
                "alphaMattingForegroundThreshold": 240,
                "alphaMattingBackgroundThreshold": 10,
                "alphaMattingErodeSize": 10
            }
        }
    ]
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    print(f"Sending background removal request...")
    response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
    response.raise_for_status()
    
    data = response.json()
    
    if "errors" in data and data["errors"]:
        raise Exception(f"API Error: {data['errors']}")
    
    if "data" not in data or not data["data"]:
        raise Exception(f"No data in response: {data}")
    
    result = data["data"][0]
    image_url = result["imageURL"]
    
    # Download the result
    print(f"Downloading result from {image_url[:60]}...")
    img_response = requests.get(image_url, timeout=60)
    img_response.raise_for_status()
    
    with open(output_path, "wb") as f:
        f.write(img_response.content)
    
    print(f"✅ Background removed! Saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    input_logo = "/root/trendscope/remotion/public/assets/scene1/trendscope-logo-white.png"
    output_logo = "/root/trendscope/remotion/public/assets/scene1/trendscope-logo-transparent.png"
    
    remove_background(input_logo, output_logo)
