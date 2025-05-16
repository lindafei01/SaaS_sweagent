
#!/usr/bin/env python3
import requests
import json
import time
import subprocess
import sys
import os

# Start the Flask app in the background
print("Starting Flask app...")
flask_process = subprocess.Popen(["python", "app.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Wait for the server to start
time.sleep(2)

# Test cases
test_cases = [
    {
        "name": "Valid TypeScript with error",
        "payload": {
            "fileName": "background.ts",
            "fileContent": "let x = y * 2;"
        },
        "expected_status": 200,
        "expected_has_error": True
    },
    {
        "name": "Valid TypeScript without error",
        "payload": {
            "fileName": "main.ts",
            "fileContent": "let x = 2 * 15;"
        },
        "expected_status": 200,
        "expected_has_error": False
    },
    {
        "name": "Valid C++ with error",
        "payload": {
            "fileName": "main.cpp",
            "fileContent": "void main() { undeclared_variable = 5; return 0; }"
        },
        "expected_status": 200,
        "expected_has_error": True
    },
    {
        "name": "Valid C++ without error",
        "payload": {
            "fileName": "main.cpp",
            "fileContent": "int main() { return 0; }"
        },
        "expected_status": 200,
        "expected_has_error": False
    },
    {
        "name": "Unsupported file type",
        "payload": {
            "fileName": "main.py",
            "fileContent": "print('Hello, world!')"
        },
        "expected_status": 400,
        "expected_has_error": True
    },
    {
        "name": "Missing fileName",
        "payload": {
            "fileContent": "let x = 2 * 15;"
        },
        "expected_status": 400,
        "expected_has_error": True
    }
]

# Run the tests
success_count = 0
failure_count = 0

for test_case in test_cases:
    print(f"\nRunning test: {test_case['name']}")
    try:
        response = requests.post(
            "http://0.0.0.0:5000/compile",
            json=test_case["payload"],
            timeout=5
        )
        
        # Check status code
        status_match = response.status_code == test_case["expected_status"]
        print(f"Status code: {response.status_code} (Expected: {test_case['expected_status']}) - {'✓' if status_match else '✗'}")
        
        # Check response content
        if response.status_code == 200:
            data = response.json()
            has_error_match = data["hasError"] == test_case["expected_has_error"]
            print(f"hasError: {data['hasError']} (Expected: {test_case['expected_has_error']}) - {'✓' if has_error_match else '✗'}")
            print(f"compilerError: {data['compilerError']}")
            
            if status_match and has_error_match:
                success_count += 1
            else:
                failure_count += 1
        else:
            if status_match:
                success_count += 1
            else:
                failure_count += 1
    except Exception as e:
        print(f"Error: {e}")
        failure_count += 1

# Print summary
print(f"\nTest Summary: {success_count} passed, {failure_count} failed")

# Terminate the Flask app
flask_process.terminate()
print("Flask app terminated.")

# Exit with appropriate status code
sys.exit(1 if failure_count > 0 else 0)