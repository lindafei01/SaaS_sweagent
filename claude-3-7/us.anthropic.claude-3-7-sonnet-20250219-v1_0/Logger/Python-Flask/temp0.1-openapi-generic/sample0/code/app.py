
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# File to store logs
LOG_FILE = "logs.txt"

# Ensure log file exists
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w') as f:
        pass  # Create empty file if it doesn't exist

@app.route('/log', methods=['POST'])
def log_message():
    """Log a message to the server."""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or 'message' not in data or not isinstance(data['message'], str):
            return jsonify({"error": "Invalid request. 'message' field is required and must be a string."}), 400
        
        message = data['message']
        
        # Write message to log file
        with open(LOG_FILE, 'a') as f:
            f.write(message + '\n')
        
        return jsonify({"status": "success"}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    """Retrieve all logged messages."""
    try:
        # Read all logs from file
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                logs = f.read()
        else:
            logs = ""
        
        return logs, 200, {'Content-Type': 'text/plain'}
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)