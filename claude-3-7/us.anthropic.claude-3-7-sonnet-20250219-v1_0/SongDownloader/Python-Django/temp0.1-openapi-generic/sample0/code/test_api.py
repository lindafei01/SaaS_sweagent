
import requests
import json

def test_download_endpoint():
    """
    Test the download endpoint with a valid file.
    """
    url = "http://localhost:5000/download"
    headers = {"Content-Type": "application/json"}
    data = {"filename": "test_song.mp3"}
    
    print("Testing download endpoint with valid file...")
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("Success! Received audio data.")
            print(f"Content type: {response.headers.get('Content-Type')}")
            print(f"Content length: {len(response.content)} bytes")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {str(e)}")
    
    print("\nTesting download endpoint with non-existent file...")
    data = {"filename": "nonexistent.mp3"}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Exception: {str(e)}")

if __name__ == "__main__":
    test_download_endpoint()