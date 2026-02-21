#!/usr/bin/env python3
"""
Generate all video assets for Trendscope Bloomberg Improvement Plan
Uses Runware API to generate multiple variations of each asset
"""

import requests
import json
import time
import os
import sys
from uuid import uuid4
from pathlib import Path

# Runware API configuration
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
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        
        data = response.json()
        
        if "data" in data and len(data["data"]) > 0:
            return data["data"]
        else:
            print(f"  Warning: No data in response: {data}")
            return []
    except Exception as e:
        print(f"  Error generating image: {e}")
        return []

def download_image(url, filepath):
    """Download image from URL to filepath"""
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"  Error downloading image: {e}")
        return False

def process_asset(asset, base_output_dir):
    """Process a single asset - generate variations"""
    
    asset_id = asset["id"]
    folder = asset["folder"]
    filename = asset["filename"]
    prompt = asset["prompt"]
    width = asset["width"]
    height = asset["height"]
    format_ext = asset["format"]
    model = asset.get("model", "runware:101@1")
    for_option = asset.get("for", "Both")
    
    output_dir = os.path.join(base_output_dir, folder)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"Asset: {asset_id}")
    print(f"For: {for_option}")
    print(f"Output: {output_dir}")
    print(f"{'='*60}")
    
    # Generate 3 variations
    print(f"Generating 3 variations...")
    results = generate_image(
        prompt=prompt,
        width=width,
        height=height,
        model=model,
        output_format=format_ext,
        number_results=3
    )
    
    if not results:
        print(f"  FAILED to generate {asset_id}")
        return False
    
    downloaded = []
    for i, result in enumerate(results):
        if "imageURL" in result:
            filepath = os.path.join(output_dir, f"{filename}_var{i+1}.{format_ext}")
            if download_image(result["imageURL"], filepath):
                downloaded.append(filepath)
                print(f"  ✓ Downloaded: {os.path.basename(filepath)}")
    
    print(f"  Generated {len(downloaded)}/3 variations")
    
    # Add a README for each asset
    readme_path = os.path.join(output_dir, "README.txt")
    with open(readme_path, 'w') as f:
        f.write(f"Asset: {asset_id}\n")
        f.write(f"Filename base: {filename}\n")
        f.write(f"For: {for_option}\n")
        f.write(f"Variations: {len(downloaded)}\n\n")
        f.write("Naming convention:\n")
        f.write("- var1, var2, var3 = different variations\n")
        f.write("- To mark best option: rename to _BEST_{filename}.{ext}\n")
    
    return len(downloaded) > 0

def main():
    """Main function to generate all assets"""
    
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    plan_path = os.path.join(script_dir, "enhanced_videos", "asset_plan.json")
    output_dir = os.path.join(script_dir, "enhanced_videos")
    
    # Load asset plan
    print(f"Loading asset plan from: {plan_path}")
    with open(plan_path, 'r') as f:
        plan = json.load(f)
    
    assets = plan["assets"]
    print(f"Found {len(assets)} assets to generate\n")
    
    # Track results
    successful = []
    failed = []
    
    # Process each asset
    for i, asset in enumerate(assets, 1):
        print(f"\n[{i}/{len(assets)}] Processing asset...")
        
        if process_asset(asset, output_dir):
            successful.append(asset["id"])
        else:
            failed.append(asset["id"])
        
        # Small delay between assets to avoid rate limiting
        if i < len(assets):
            time.sleep(2)
    
    # Summary
    print(f"\n{'='*60}")
    print("GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"Successful: {len(successful)}/{len(assets)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        print(f"\nGenerated assets:")
        for aid in successful:
            print(f"  ✓ {aid}")
    
    if failed:
        print(f"\nFailed assets:")
        for aid in failed:
            print(f"  ✗ {aid}")
    
    print(f"\nOutput directory: {output_dir}")
    print("\nNext steps:")
    print("1. Review each asset folder")
    print("2. Select the best variation for each asset")
    print("3. Rename the best option to: _BEST_{filename}.{ext}")
    print("4. Update the improvement plan with selected assets")
    
    return len(failed) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
