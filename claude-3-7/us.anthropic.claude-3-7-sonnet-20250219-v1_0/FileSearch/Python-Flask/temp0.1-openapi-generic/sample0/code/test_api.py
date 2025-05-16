
#!/usr/bin/env python3
import requests
import json
import sys

def test_search_api():
    """Test the search API with different parameters"""
    base_url = "http://0.0.0.0:5000/search"
    
    # Test 1: Search by content
    print("Test 1: Search by content 'Hello World'")
    payload = {"search_content": "Hello World"}
    response = requests.post(base_url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()
    
    # Test 2: Search by filename
    print("Test 2: Search by filename 'file1'")
    payload = {"search_filename": "file1"}
    response = requests.post(base_url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()
    
    # Test 3: Search in specific directory
    print("Test 3: Search in /songs directory")
    payload = {"search_content": "Hello", "search_dir": "/songs"}
    response = requests.post(base_url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()
    
    # Test 4: Invalid request (no search parameters)
    print("Test 4: Invalid request (no search parameters)")
    payload = {"search_dir": "/songs"}
    response = requests.post(base_url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    test_search_api()