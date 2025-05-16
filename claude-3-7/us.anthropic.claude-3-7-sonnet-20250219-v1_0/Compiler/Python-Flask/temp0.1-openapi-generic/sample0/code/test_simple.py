
#!/usr/bin/env python3
import requests
import json
import time
import subprocess
import sys
import threading

def start_flask_app():
    subprocess.run(["python", "app.py"])

# Start the Flask app in a separate thread
print("Starting Flask app...")
flask_thread = threading.Thread(target=start_flask_app)
flask_thread.daemon = True
flask_thread.start()

# Wait for the server to start
print("Waiting for server to start...")
time.sleep(2)

# Test a simple request
try:
    print("Testing API...")
    response = requests.post(
        "http://0.0.0.0:5000/compile",
        json={
            "fileName": "test.ts",
            "fileContent": "let x = 2;"
        }
    )
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.text}")
    print("Test completed.")
except Exception as e:
    print(f"Error: {e}")

print("Test script completed.")