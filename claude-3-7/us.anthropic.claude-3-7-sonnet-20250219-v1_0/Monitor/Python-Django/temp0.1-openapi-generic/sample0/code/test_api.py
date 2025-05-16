
import requests
import json
import sys

def test_monitor_commands():
    """Test the monitor/commands endpoint"""
    url = "http://localhost:5000/monitor/commands"
    
    # Test with valid data
    data = {
        "command_regex": "python.*",
        "filter_flags": "aux"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("Response data:")
            processes = response.json()
            for process in processes[:5]:  # Show only first 5 processes
                print(f"PID: {process['processId']}, Process: {process['processString'][:50]}...")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error making request: {str(e)}")
        
    # Test with missing required field
    print("\nTesting with missing required field:")
    data = {
        "filter_flags": "aux"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error making request: {str(e)}")

if __name__ == "__main__":
    print("Testing monitor/commands API endpoint...")
    test_monitor_commands()
    print("Test completed.")