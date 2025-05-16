
import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_log_endpoint():
    print("Testing POST /log endpoint...")
    response = requests.post(
        f"{BASE_URL}/log",
        json={"message": "This is a test log message"}
    )
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("POST /log test passed!")

def test_logs_endpoint():
    print("\nTesting GET /logs endpoint...")
    response = requests.get(f"{BASE_URL}/logs")
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    assert response.status_code == 200
    assert "This is a test log message" in response.text
    print("GET /logs test passed!")

if __name__ == "__main__":
    print("Waiting for server to start...")
    time.sleep(2)  # Give the server time to start
    
    try:
        test_log_endpoint()
        test_logs_endpoint()
        print("\nAll tests passed!")
    except Exception as e:
        print(f"\nTest failed: {str(e)}")