
import requests
import json
import time
import subprocess
import os
import signal
import sys

# Start the Flask app in the background
print("Starting Flask app in the background...")
flask_process = subprocess.Popen(["python", "app.py"], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE)

# Give the app time to start
time.sleep(2)

# Base URL for the API
base_url = "http://0.0.0.0:5000"

try:
    # Test POST /log endpoint
    print("\nTesting POST /log endpoint...")
    log_response = requests.post(
        f"{base_url}/log",
        json={"message": "This is a test log message"}
    )
    print(f"Status code: {log_response.status_code}")
    print(f"Response: {log_response.json()}")
    
    # Test another log message
    log_response = requests.post(
        f"{base_url}/log",
        json={"message": "This is another test log message"}
    )
    print(f"Status code: {log_response.status_code}")
    print(f"Response: {log_response.json()}")
    
    # Test GET /logs endpoint
    print("\nTesting GET /logs endpoint...")
    logs_response = requests.get(f"{base_url}/logs")
    print(f"Status code: {logs_response.status_code}")
    print(f"Response: {logs_response.text}")
    
    print("\nAll tests completed successfully!")
    
except Exception as e:
    print(f"Error during testing: {e}")
    
finally:
    # Terminate the Flask app
    print("\nTerminating Flask app...")
    flask_process.terminate()
    flask_process.wait()
    print("Flask app terminated.")