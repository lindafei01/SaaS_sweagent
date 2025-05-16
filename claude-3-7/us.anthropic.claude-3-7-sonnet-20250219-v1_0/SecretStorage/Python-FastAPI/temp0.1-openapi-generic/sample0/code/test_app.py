
import requests
import json
import time

# Base URL for the API
BASE_URL = "http://0.0.0.0:5000"

def test_register():
    print("Testing registration...")
    url = f"{BASE_URL}/register"
    data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword"
    }
    response = requests.post(url, json=data)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 201

def test_login():
    print("\nTesting login...")
    url = f"{BASE_URL}/login"
    data = {
        "email": "test@example.com",
        "password": "testpassword"
    }
    response = requests.post(url, json=data)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        return response.json().get("token")
    return None

def test_set_secret(token):
    print("\nTesting set_secret...")
    url = f"{BASE_URL}/set_secret"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "username": "testuser",
        "secret": "my test secret"
    }
    response = requests.post(url, json=data, headers=headers)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_get_secret(token):
    print("\nTesting get_secret...")
    url = f"{BASE_URL}/get_secret?username=testuser"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def run_tests():
    print("Starting API tests...")
    
    # Test registration
    registration_success = test_register()
    if not registration_success:
        print("Registration test failed!")
        return
    
    # Test login
    token = test_login()
    if not token:
        print("Login test failed!")
        return
    
    # Test set_secret
    set_secret_success = test_set_secret(token)
    if not set_secret_success:
        print("Set secret test failed!")
        return
    
    # Test get_secret
    get_secret_success = test_get_secret(token)
    if not get_secret_success:
        print("Get secret test failed!")
        return
    
    print("\nAll tests passed successfully!")

if __name__ == "__main__":
    # Wait for the server to start
    print("Waiting for server to start...")
    time.sleep(2)
    run_tests()