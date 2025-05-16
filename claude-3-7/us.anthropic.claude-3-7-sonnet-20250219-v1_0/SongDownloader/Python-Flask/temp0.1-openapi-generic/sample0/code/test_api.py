
#!/usr/bin/env python3
"""
Test script for the Song Downloader API
"""

import os
import requests
import json

# Create a test song file if it doesn't exist
SONGS_DIR = "/var/songs"
TEST_SONG_NAME = "test_song.mp3"
TEST_SONG_PATH = os.path.join(SONGS_DIR, TEST_SONG_NAME)

# Create songs directory if it doesn't exist
os.makedirs(SONGS_DIR, exist_ok=True)

# Create a simple test file if it doesn't exist
if not os.path.exists(TEST_SONG_PATH):
    with open(TEST_SONG_PATH, 'wb') as f:
        # Write some dummy binary data to simulate an MP3 file
        f.write(b'\xFF\xFB\x90\x44\x00\x00\x00\x00\x00\x00\x00\x00')
    print(f"Created test song file: {TEST_SONG_PATH}")
else:
    print(f"Test song file already exists: {TEST_SONG_PATH}")

# Test the API (this would be run after the Flask app is started)
def test_download_endpoint():
    """Test the /download endpoint"""
    print("\nTesting /download endpoint...")
    
    # Test with valid file
    print("\n1. Testing with valid file...")
    payload = {"filename": TEST_SONG_NAME}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(
            "http://0.0.0.0:5000/download", 
            data=json.dumps(payload), 
            headers=headers
        )
        print(f"Status code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Content-Length: {response.headers.get('Content-Length')} bytes")
        
        if response.status_code == 200:
            print("✅ Test passed: Valid file download successful")
        else:
            print("❌ Test failed: Valid file download unsuccessful")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    
    # Test with non-existent file
    print("\n2. Testing with non-existent file...")
    payload = {"filename": "non_existent_file.mp3"}
    
    try:
        response = requests.post(
            "http://0.0.0.0:5000/download", 
            data=json.dumps(payload), 
            headers=headers
        )
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 404:
            print("✅ Test passed: Non-existent file correctly returns 404")
        else:
            print("❌ Test failed: Non-existent file should return 404")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    
    # Test with path traversal attempt
    print("\n3. Testing with path traversal attempt...")
    payload = {"filename": "../../../etc/passwd"}
    
    try:
        response = requests.post(
            "http://0.0.0.0:5000/download", 
            data=json.dumps(payload), 
            headers=headers
        )
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 400 or response.status_code == 404:
            print("✅ Test passed: Path traversal correctly prevented")
        else:
            print("❌ Test failed: Path traversal not prevented")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

print("Test script prepared. Run the Flask app first, then run this script to test the API.")
print("To run the Flask app: python app.py")
print("To run this test script: python test_api.py")

# Uncomment to run tests automatically if the Flask app is already running
# if __name__ == "__main__":
#     test_download_endpoint()