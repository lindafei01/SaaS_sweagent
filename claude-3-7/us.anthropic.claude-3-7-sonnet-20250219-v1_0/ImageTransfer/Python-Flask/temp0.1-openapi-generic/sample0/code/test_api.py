
#!/usr/bin/env python3
import requests
import os
import sys
from io import BytesIO
from PIL import Image

def create_test_image():
    """Create a simple test image."""
    img = Image.new('RGB', (100, 100), color='red')
    img_io = BytesIO()
    img.save(img_io, 'JPEG')
    img_io.seek(0)
    return img_io

def test_api():
    """Test the image upload and retrieval API."""
    print("Testing API...")
    
    # Test the index endpoint
    try:
        response = requests.get('http://0.0.0.0:5000/')
        if response.status_code == 200:
            print("✓ Index endpoint works")
        else:
            print(f"✗ Index endpoint failed with status code {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error accessing index endpoint: {str(e)}")
        print("Make sure the Flask server is running on port 5000")
        return False
    
    # Test image upload
    try:
        img_io = create_test_image()
        files = {'file': ('test.jpg', img_io, 'image/jpeg')}
        response = requests.post('http://0.0.0.0:5000/upload', files=files)
        
        if response.status_code == 200 and 'id' in response.json():
            image_id = response.json()['id']
            print(f"✓ Upload endpoint works. Image ID: {image_id}")
        else:
            print(f"✗ Upload endpoint failed with status code {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"✗ Error uploading image: {str(e)}")
        return False
    
    # Test image retrieval
    try:
        response = requests.get(f'http://0.0.0.0:5000/images/{image_id}')
        
        if response.status_code == 200 and response.headers.get('Content-Type') == 'image/jpeg':
            print("✓ Image retrieval endpoint works")
        else:
            print(f"✗ Image retrieval endpoint failed with status code {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"✗ Error retrieving image: {str(e)}")
        return False
    
    print("All tests passed successfully!")
    return True

if __name__ == "__main__":
    print("This script tests the Image Upload and Share API.")
    print("Note: This test assumes the Flask server is running on 0.0.0.0:5000")
    
    # Run the test
    test_api()