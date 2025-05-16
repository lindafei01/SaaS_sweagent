
#!/usr/bin/env python3
"""
Song Downloader API

A simple Flask API for streaming songs from the server's /var/songs directory.
"""

import os
from flask import Flask, request, send_file, jsonify
from werkzeug.utils import secure_filename
import pathlib

# Initialize Flask app
app = Flask(__name__)

# Configuration
SONGS_DIRECTORY = "/var/songs"
ALLOWED_EXTENSIONS = {"mp3", "wav", "ogg", "flac"}

# Ensure the songs directory exists
os.makedirs(SONGS_DIRECTORY, exist_ok=True)

def is_safe_path(base_dir, requested_path):
    """
    Check if the requested path is safe (doesn't try to access files outside the base directory)
    
    Args:
        base_dir (str): The base directory that should contain all accessible files
        requested_path (str): The path requested by the user
        
    Returns:
        bool: True if the path is safe, False otherwise
    """
    # Resolve to absolute paths
    base_dir_abs = os.path.abspath(base_dir)
    requested_path_abs = os.path.abspath(os.path.join(base_dir, requested_path))
    
    # Check if the requested path is within the base directory
    return os.path.commonpath([base_dir_abs]) == os.path.commonpath([base_dir_abs, requested_path_abs])

def allowed_file(filename):
    """
    Check if the file has an allowed extension
    
    Args:
        filename (str): The filename to check
        
    Returns:
        bool: True if the file has an allowed extension, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/download', methods=['POST'])
def download_song():
    """
    Endpoint to download/stream a song from the server
    
    Request body:
        filename (str): The name of the song file to download
        
    Returns:
        200: Stream of the song file
        400: Invalid input (missing filename or invalid format)
        404: File not found
    """
    # Check if request has JSON data
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    # Get filename from request
    data = request.get_json()
    if 'filename' not in data:
        return jsonify({"error": "Missing filename parameter"}), 400
    
    filename = data['filename']
    
    # Validate filename
    if not filename or not isinstance(filename, str):
        return jsonify({"error": "Invalid filename"}), 400
    
    # Secure the filename to prevent path traversal attacks
    secure_name = secure_filename(filename)
    
    # Check if the file exists and is within the songs directory
    file_path = os.path.join(SONGS_DIRECTORY, secure_name)
    
    if not is_safe_path(SONGS_DIRECTORY, secure_name):
        return jsonify({"error": "Invalid file path"}), 400
    
    if not os.path.isfile(file_path):
        return jsonify({"error": "File not found"}), 404
    
    # Determine the MIME type based on file extension
    mime_type = "audio/mpeg"  # Default to audio/mpeg
    if secure_name.endswith('.wav'):
        mime_type = "audio/wav"
    elif secure_name.endswith('.ogg'):
        mime_type = "audio/ogg"
    elif secure_name.endswith('.flac'):
        mime_type = "audio/flac"
    
    # Stream the file to the client
    return send_file(
        file_path,
        mimetype=mime_type,
        as_attachment=True,
        download_name=secure_name
    )

if __name__ == '__main__':
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)