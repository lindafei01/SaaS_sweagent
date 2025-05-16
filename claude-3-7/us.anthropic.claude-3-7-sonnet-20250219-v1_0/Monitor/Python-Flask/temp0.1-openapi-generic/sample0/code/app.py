
#!/usr/bin/env python3
"""
Monitor Service - A Flask application that monitors running processes on the server.
"""

import re
import subprocess
import json
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)

# Add security headers to all responses
@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/monitor/commands', methods=['POST', 'OPTIONS'])
def monitor_commands():
    """
    Endpoint to retrieve a list of running processes that match a given regex.
    """
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return make_response('', 200)
        
    # Get request data
    data = request.get_json()
    
    # Validate required fields
    if not data or 'command_regex' not in data:
        return jsonify({"code": 400, "message": "Missing required field: command_regex"}), 400
    
    command_regex = data.get('command_regex')
    filter_flags = data.get('filter_flags', 'aux')
    
    try:
        # Validate regex pattern
        re.compile(command_regex)
    except re.error:
        return jsonify({"code": 400, "message": "Invalid regular expression"}), 400
    
    # Sanitize filter_flags to prevent command injection
    # Only allow alphanumeric characters, spaces, and certain special characters
    if not re.match(r'^[a-zA-Z0-9\s\-]+$', filter_flags):
        return jsonify({"code": 400, "message": "Invalid filter flags"}), 400
    
    try:
        # Execute ps command with the provided flags
        cmd = ['ps', *filter_flags.split()]
        process = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = process.stdout
        
        # Process the output
        lines = output.strip().split('\n')
        result = []
        
        # Skip the header line
        for line in lines[1:]:
            try:
                # Extract process ID and command string
                parts = line.split(None, 10)  # Split by whitespace, max 10 splits
                if len(parts) >= 2:
                    pid = parts[1]  # PID is in the second column
                    process_string = line
                    
                    # Check if the command matches the regex
                    if re.search(command_regex, process_string):
                        try:
                            pid_int = int(pid)
                            result.append({
                                "processId": pid_int,
                                "processString": process_string.strip()
                            })
                        except ValueError:
                            # Skip if PID is not a valid integer
                            continue
            except Exception as e:
                # Skip lines that can't be processed
                continue
        
        return jsonify(result)
    
    except subprocess.CalledProcessError as e:
        return jsonify({"code": 500, "message": f"Error executing process command: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"code": 500, "message": f"Internal server error: {str(e)}"}), 500

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"code": 400, "message": "Bad request"}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"code": 404, "message": "Resource not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"code": 405, "message": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({"code": 500, "message": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)