
#!/usr/bin/env python3
import json
import time
import subprocess
import sys
import signal
import os
import http.client
from multiprocessing import Process

def start_server():
    """Start the FastAPI server in a separate process"""
    subprocess.run(["python", "app.py"])

def test_monitor_endpoint():
    """Test the /monitor/commands endpoint"""
    print("Testing /monitor/commands endpoint...")
    
    # Wait for server to start
    time.sleep(2)
    
    # Test with a simple regex that should match some processes
    payload = {
        "command_regex": "python.*"
    }
    
    try:
        # Create a connection to the server
        conn = http.client.HTTPConnection("0.0.0.0", 5000)
        
        # Send the request
        headers = {"Content-Type": "application/json"}
        conn.request("POST", "/monitor/commands", json.dumps(payload), headers)
        
        # Get the response
        response = conn.getresponse()
        status = response.status
        response_data = response.read().decode()
        
        print(f"Status Code: {status}")
        if status == 200:
            data = json.loads(response_data)
            print(f"Found {len(data)} matching processes")
            if len(data) > 0:
                print("Sample process:")
                print(json.dumps(data[0], indent=2))
            return True
        else:
            print(f"Error: {response_data}")
            return False
    except Exception as e:
        print(f"Request failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Start server in a separate process
    server_process = Process(target=start_server)
    server_process.start()
    
    try:
        # Run the test
        success = test_monitor_endpoint()
        
        # Print result
        if success:
            print("\nTest completed successfully!")
        else:
            print("\nTest failed!")
            
    finally:
        # Clean up: terminate the server process
        server_process.terminate()
        server_process.join(timeout=1)
        
        # If process is still alive, kill it
        if server_process.is_alive():
            os.kill(server_process.pid, signal.SIGKILL)
            server_process.join()