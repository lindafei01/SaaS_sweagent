
import requests
import sys

def test_download_song():
    url = "http://0.0.0.0:5000/download"
    
    # Test with a valid file
    valid_data = {"filename": "test_song.mp3"}
    print(f"Testing with valid file: {valid_data}")
    try:
        response = requests.post(url, json=valid_data)
        print(f"Status code: {response.status_code}")
        print(f"Content type: {response.headers.get('content-type')}")
        print(f"Content length: {len(response.content)} bytes")
        print(f"Content: {response.content[:30]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test with a non-existent file
    invalid_data = {"filename": "nonexistent.mp3"}
    print(f"\nTesting with non-existent file: {invalid_data}")
    try:
        response = requests.post(url, json=invalid_data)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test with a path traversal attempt
    traversal_data = {"filename": "../../../etc/passwd"}
    print(f"\nTesting with path traversal attempt: {traversal_data}")
    try:
        response = requests.post(url, json=traversal_data)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_download_song()