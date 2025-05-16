
import requests
import datetime
import time
import json

def test_api():
    print("Testing Click Tracking API")
    
    # Test registering a click
    print("\nTesting POST /click")
    response = requests.post('http://localhost:5000/click')
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Wait a moment to ensure the click is registered
    time.sleep(1)
    
    # Test retrieving clicks after a date
    print("\nTesting GET /clicks with direction >")
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    response = requests.get(f'http://localhost:5000/clicks?date={yesterday}&direction=>')
    print(f"Status code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    
    # Test retrieving clicks before a date
    print("\nTesting GET /clicks with direction <")
    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    response = requests.get(f'http://localhost:5000/clicks?date={tomorrow}&direction=<')
    print(f"Status code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    
    # Test invalid request
    print("\nTesting invalid request")
    response = requests.get('http://localhost:5000/clicks?date=invalid&direction=<')
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    print("This script tests the Click Tracking API.")
    print("Make sure the server is running on http://localhost:5000 before executing this script.")
    print("You can run the server with: python manage.py runserver 0.0.0.0:5000")
    print("This script is for manual testing only and is not part of the automated tests.")