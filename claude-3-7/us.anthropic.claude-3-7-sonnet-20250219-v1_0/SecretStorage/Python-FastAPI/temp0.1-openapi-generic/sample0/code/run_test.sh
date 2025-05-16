
#!/bin/bash

# Start the server in the background
python app.py &
SERVER_PID=$!

# Wait for the server to start
sleep 2

# Run the test script
python test_app.py

# Kill the server process
kill $SERVER_PID