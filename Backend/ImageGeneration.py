import asyncio
from random import randint
from PIL import Image
import requests
import os
import time
from time import sleep

# Ensure the Data folder exists
os.makedirs("Data", exist_ok=True)

# Function to open and display images based on a given prompt
def open_images(prompt):
    folder_path = "Data"  # Folder where images are stored
    filename_prefix = prompt.replace(" ", "_")  # Create valid filename
    
    # Generate the filenames for the images
    Files = [f"{filename_prefix}{i}.jpg" for i in range(1, 5)]

    for jpg_file in Files:
        image_path = os.path.join(folder_path, jpg_file)
        try:
            img = Image.open(image_path)
            print(f"Opening image: {image_path}")
            img.show()
            sleep(1)  # Pause between images
        except IOError:
            print(f"Unable to open {image_path}")

# API configuration
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
API_KEY = "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"
headers = {"Authorization": f"Bearer {API_KEY}"}

async def query(payload):
    response = await asyncio.to_thread(requests.post, API_URL, headers=headers, json=payload)
    return response.content if response.status_code == 200 else None

async def generate_images(prompt: str):
    tasks = []
    for _ in range(4):  # Create 4 images
        payload = {
            "inputs": f"{prompt}, quality=4K, sharpness=maximum, Ultra High details, high resolution, seed={randint(0, 1000000)}",
        }
        tasks.append(asyncio.create_task(query(payload)))

    image_bytes_list = await asyncio.gather(*tasks)
    
    # Save images with proper error handling
    filename_prefix = prompt.replace(" ", "_")
    for i, image_bytes in enumerate(image_bytes_list):
        if image_bytes:
            try:
                with open(f"Data/{filename_prefix}{i + 1}.jpg", "wb") as f:
                    f.write(image_bytes)
            except IOError as e:
                print(f"Failed to save image {i+1}: {e}")
generate_images
def GenerateImages(prompt: str):
    asyncio.run(generate_images(prompt))
    open_images(prompt)

def main():
    timeout = 60 * 5  # 5 minute timeout
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            # Read and validate input file
            if not os.path.exists("Frontend/Files/ImageGeneration.data"):
                sleep(1)
                continue
                
            with open("Frontend/Files/ImageGeneration.data", "r") as f:
                data = f.read().strip()
            
            # Validate data format
            if ":" not in data:
                print("Waiting for valid input (format: 'PROMPT:STATUS')...")
                sleep(1)
                continue
                
            prompt, status = data.split(":", 1)  # Split on first colon
            
            if status == "True":
                print(f"Generating images for: {prompt}")
                GenerateImages(prompt)
                
                # Update status
                with open("Frontend/Files/ImageGeneration.data", "w") as f:
                    f.write(f"{prompt}:False")
                break
                
            sleep(1)
            
        except Exception as e:
            print(f"Error: {str(e)}")
            sleep(1)
    else:
        print("Timeout reached after 5 minutes")

if __name__ == "__main__":
    # Ensure required directories exist
    os.makedirs("Frontend/Files", exist_ok=True)
    
    # Initialize file if it doesn't exist
    if not os.path.exists("Frontend/Files/ImageGeneration.data"):
        with open("Frontend/Files/ImageGeneration.data", "w") as f:
            f.write("sample_prompt:False")
    
    main()