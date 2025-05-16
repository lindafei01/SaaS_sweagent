
#!/usr/bin/env python3
import os
import re
import json
from flask import Flask, request, jsonify, Response
from werkzeug.exceptions import BadRequest

app = Flask(__name__)

# Base directory for file searches
DATA_DIR = "/data"

# Configure Flask for better security
app.config['JSON_SORT_KEYS'] = False  # Preserve key order in JSON responses
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024  # Limit request size to 16KB

# Add security headers to all responses
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

@app.route('/search', methods=['POST'])
def search_files():
    """
    Search for files in the data directory based on content or filename.
    
    Request body should contain:
    - search_content: String to search for within files
    - search_filename: String to match against filenames
    - search_dir: Optional subdirectory within /data to search in
    
    Returns a list of file paths that match the criteria.
    """
    try:
        # Parse request data
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "Invalid JSON data"}), 400
        except BadRequest:
            return jsonify({"error": "Invalid JSON format"}), 400
        
        search_content = data.get('search_content')
        search_filename = data.get('search_filename')
        search_dir = data.get('search_dir')
        
        # Validate input
        if not search_content and not search_filename:
            return jsonify({"error": "At least one of search_content or search_filename must be provided"}), 400
        
        # Determine the search directory
        base_search_dir = DATA_DIR
        if search_dir:
            # Validate search_dir is a string
            if not isinstance(search_dir, str):
                return jsonify({"error": "search_dir must be a string"}), 400
                
            # Sanitize the search_dir to prevent directory traversal attacks
            search_dir = search_dir.lstrip('/')
            # Ensure we're only searching within the data directory
            base_search_dir = os.path.join(DATA_DIR, search_dir)
            
            # Validate that the search directory is within the data directory
            real_base_path = os.path.realpath(DATA_DIR)
            real_search_path = os.path.realpath(base_search_dir)
            if not real_search_path.startswith(real_base_path):
                return jsonify({"error": "Invalid search directory"}), 400
        
        # Check if the directory exists
        if not os.path.exists(base_search_dir):
            return jsonify({"files": []}), 200
        
        # Perform the search
        matching_files = []
        
        for root, _, files in os.walk(base_search_dir):
            for filename in files:
                file_path = os.path.join(root, filename)
                
                # Check if filename matches
                if search_filename and filename.startswith(search_filename):
                    matching_files.append(file_path)
                    continue
                
                # Check if content matches
                if search_content:
                    try:
                        # Try to read as text first
                        with open(file_path, 'r', errors='ignore') as f:
                            content = f.read()
                            if search_content in content:
                                matching_files.append(file_path)
                                continue
                                
                        # If not found in text mode, try binary mode for more thorough search
                        if file_path not in matching_files:
                            with open(file_path, 'rb') as f:
                                binary_content = f.read()
                                if search_content.encode('utf-8', errors='ignore') in binary_content:
                                    matching_files.append(file_path)
                    except Exception:
                        # Skip files that can't be read
                        continue
        
        # Format the response
        return jsonify({"files": matching_files})
    
    except Exception as e:
        app.logger.error(f"Error in search_files: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)