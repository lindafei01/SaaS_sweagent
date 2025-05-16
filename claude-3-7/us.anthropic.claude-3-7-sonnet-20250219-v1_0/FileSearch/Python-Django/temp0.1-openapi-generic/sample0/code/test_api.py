
import os
import requests
import json
import tempfile
import time
import subprocess
import signal
import sys
import atexit

# Create test data directory
temp_dir = tempfile.TemporaryDirectory()
os.environ['DATA_DIR'] = temp_dir.name
print(f"Created temporary data directory: {temp_dir.name}")

# Create test files
file1_path = os.path.join(temp_dir.name, 'file1.txt')
with open(file1_path, 'w') as f:
    f.write('Hello World')
print(f"Created test file: {file1_path}")

songs_dir = os.path.join(temp_dir.name, 'songs')
os.makedirs(songs_dir, exist_ok=True)
file2_path = os.path.join(songs_dir, 'song.mp3')
with open(file2_path, 'w') as f:
    f.write('MP3 content')
print(f"Created test file: {file2_path}")

# Start Django server in a separate process
print("Starting Django server...")
server_process = subprocess.Popen(
    ["python", "manage.py", "runserver", "0.0.0.0:5000"],
    env=dict(os.environ, DATA_DIR=temp_dir.name)
)

# Register cleanup function
def cleanup():
    print("Cleaning up...")
    if server_process:
        print("Stopping Django server...")
        server_process.terminate()
        server_process.wait()
    temp_dir.cleanup()
    print("Cleanup complete")

atexit.register(cleanup)

# Wait for server to start
print("Waiting for server to start...")
time.sleep(3)

# Test the API
base_url = "http://0.0.0.0:5000"

print("\nTesting search by content...")
response = requests.post(
    f"{base_url}/search",
    json={"search_content": "Hello World"}
)
print(f"Status code: {response.status_code}")
print(f"Response: {response.json()}")

print("\nTesting search by filename...")
response = requests.post(
    f"{base_url}/search",
    json={"search_filename": "song.mp3"}
)
print(f"Status code: {response.status_code}")
print(f"Response: {response.json()}")

print("\nTesting search with directory...")
response = requests.post(
    f"{base_url}/search",
    json={"search_filename": ".mp3", "search_dir": "/songs"}
)
print(f"Status code: {response.status_code}")
print(f"Response: {response.json()}")

print("\nTesting invalid input...")
response = requests.post(
    f"{base_url}/search",
    json={}
)
print(f"Status code: {response.status_code}")
print(f"Response: {response.json()}")

print("\nTests completed. Press Ctrl+C to exit.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting...")
    sys.exit(0)