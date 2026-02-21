#!/usr/bin/env python3
"""
Runware Image Generation Script
Generates images using the Runware API
"""

import requests
import json
import time
import os
from uuid import uuid4

API_KEY = "nxg6IpsRyqs0RLl7rO76EqGfTUwp6LxL"
API_URL = "https://api.runware.ai/v1"

def generate_image(prompt, width=1920, height=1088, model="runware:101@1", output_format="jpg", number_results=3):
    """Generate images using Runware API"""
    
    task_uuid = str(uuid4())
    
    payload = [
        {
            "taskType": "imageInference",
            "taskUUID": task_uuid,
            "positivePrompt": prompt,
            "model": model,
            "width": width,
            "height": height,
            "numberResults": number_results,
            "outputType": "URL",
            "outputFormat": output_format,
            "steps": 30,
            "CFGScale": 7.5
        }
    ]
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()
    
    data = response.json()
    
    if "data" in data and len(data["data"]) > 0:
        return data["data"]
    else:
        raise Exception(f"No data in response: {data}")

def download_image(url, filepath):
    """Download image from URL to filepath"""
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    with open(filepath, 'wb') as f:
        f.write(response.content)
    return filepath

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python runware_generate.py <prompt> <output_folder> <base_name>")
        sys.exit(1)
    
    prompt = sys.argv[1]
    output_folder = sys.argv[2]
    base_name = sys.argv[3]
    
    print(f"Generating images for: {base_name}")
    print(f"Prompt: {prompt[:100]}...")
    
    results = generate_image(prompt, number_results=3)
    
    os.makedirs(output_folder, exist_ok=True)
    
    downloaded = []
    for i, result in enumerate(results):
        if "imageURL" in result:
            ext = result.get("imageURL", ".jpg").split("?")[0].split(".")[-1]
            if ext not in ["jpg", "jpeg", "png", "webp"]:
                ext = "jpg"
            filepath = os.path.join(output_folder, f"{base_name}_var{i+1}.{ext}")
            download_image(result["imageURL"], filepath)
            downloaded.append(filepath)
            print(f"Downloaded: {filepath}")
    
    print(f"\nGenerated {len(downloaded)} images in {output_folder}")
