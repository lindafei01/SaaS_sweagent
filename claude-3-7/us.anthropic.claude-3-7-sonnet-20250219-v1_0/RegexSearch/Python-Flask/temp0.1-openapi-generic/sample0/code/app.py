
#!/usr/bin/env python3
import os
import re
import json
import logging
from flask import Flask, request, jsonify
import werkzeug.security

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)

# Define the root directory for files
FILES_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')

@app.route('/search', methods=['GET'])
def search_files():
    try:
        # Get query parameters
        regex_pattern = request.args.get('regex')
        if not regex_pattern:
            return jsonify({"error": "Missing required parameter: regex"}), 400
        
        directory = request.args.get('directory', '')
        recursive = request.args.get('recursive', 'false').lower() == 'true'
        
        # Validate and sanitize directory path to prevent path traversal
        search_dir = os.path.normpath(os.path.join(FILES_ROOT, directory))
        
        # Ensure the search directory is within FILES_ROOT
        if not search_dir.startswith(FILES_ROOT):
            return jsonify({"error": "Invalid directory path"}), 400
        
        # Check if directory exists
        if not os.path.isdir(search_dir):
            return jsonify({"error": f"Directory not found: {directory}"}), 400
        
        # Compile regex pattern
        try:
            pattern = re.compile(regex_pattern)
        except re.error as e:
            app.logger.error(f"Invalid regex pattern: {str(e)}")
            return jsonify({"error": f"Invalid regex pattern: {str(e)}"}), 400
        
        # Search for files matching the regex
        matching_files = []
        
        if recursive:
            # Walk through directory and subdirectories
            for root, _, files in os.walk(search_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if check_file_matches(file_path, pattern):
                        # Get relative path from search directory
                        rel_path = os.path.relpath(file_path, search_dir)
                        matching_files.append(rel_path)
        else:
            # Only search in the specified directory (non-recursive)
            for file in os.listdir(search_dir):
                file_path = os.path.join(search_dir, file)
                if os.path.isfile(file_path) and check_file_matches(file_path, pattern):
                    matching_files.append(file)
        
        return jsonify({"files": matching_files}), 200
    
    except Exception as e:
        app.logger.error(f"Error during file search: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def check_file_matches(file_path, pattern):
    """Check if file content matches the regex pattern."""
    try:
        # Only process text files
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return bool(pattern.search(content))
        except UnicodeDecodeError:
            # Skip binary files
            return False
    except Exception as e:
        app.logger.warning(f"Error reading file {file_path}: {str(e)}")
        return False

if __name__ == '__main__':
    # Ensure the files directory exists
    os.makedirs(FILES_ROOT, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=False)