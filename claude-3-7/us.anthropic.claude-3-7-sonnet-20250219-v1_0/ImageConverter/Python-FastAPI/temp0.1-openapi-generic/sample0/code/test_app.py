
import httpx
import os
import time
import subprocess
import sys
from PIL import Image
import io

# Create test images
def create_test_images():
    # Create a directory for test images
    os.makedirs("test_images", exist_ok=True)
    
    # Create 3 simple test images with different colors
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]  # Red, Green, Blue
    image_paths = []
    
    for i, color in enumerate(colors):
        img = Image.new('RGB', (100, 100), color)
        path = f"test_images/test_image_{i}.png"
        img.save(path)
        image_paths.append(path)
    
    return image_paths

def test_gif_creation():
    # Start the server in the background
    server_process = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for the server to start
    time.sleep(2)
    
    try:
        # Create test images
        image_paths = create_test_images()
        
        # Prepare files for the request
        files = []
        for path in image_paths:
            with open(path, "rb") as f:
                files.append(("images", (os.path.basename(path), f.read(), "image/png")))
        
        # Make the request
        response = httpx.post(
            "http://0.0.0.0:5000/create-gif",
            files=files,
            data={
                "targetSize": "200x200",
                "delay": "100",
                "appendReverted": "true"
            },
            timeout=10.0
        )
        
        # Check response
        if response.status_code == 200:
            print("Test passed! GIF created successfully.")
            # Save the GIF for inspection
            with open("test_output.gif", "wb") as f:
                f.write(response.content)
            print(f"GIF saved to test_output.gif (size: {len(response.content)} bytes)")
        else:
            print(f"Test failed! Status code: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"Error during test: {str(e)}")
    
    finally:
        # Clean up
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    test_gif_creation()