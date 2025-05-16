
import requests
import json

def test_calculator_api():
    url = "http://localhost:5000/calculator"
    headers = {"Content-Type": "application/json"}
    
    # Test case 1: Simple expression
    payload = {"expression": "1 + 2*3"}
    try:
        print(f"Testing expression: {payload['expression']}")
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test case 2: Complex expression
    payload = {"expression": "(10 + 5) * 2 - 8 / 4"}
    try:
        print(f"Testing expression: {payload['expression']}")
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test case 3: Invalid expression
    payload = {"expression": "1 + * 2"}
    try:
        print(f"Testing expression: {payload['expression']}")
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    print("This script tests the calculator API. Make sure the server is running first.")
    print("Run the server with: python manage.py runserver")
    print("--------------------------------------------------------------")
    test_calculator_api()