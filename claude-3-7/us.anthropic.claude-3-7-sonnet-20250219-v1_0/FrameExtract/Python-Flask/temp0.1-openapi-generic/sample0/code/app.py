
#!/usr/bin/env python3
import os
import subprocess
import tempfile
import uuid
import re
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Set maximum file size to 100MB
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# Security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to each response"""
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    # Enable XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Strict HTTPS (if using HTTPS)
    # response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Allowed video file extensions
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv'}

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def sanitize_filename(filename):
    """Sanitize filename to prevent path traversal attacks"""
    # First use secure_filename from werkzeug
    filename = secure_filename(filename)
    # Additional sanitization
    filename = re.sub(r'[^\w\.-]', '_', filename)
    return filename

@app.route('/extract', methods=['POST'])
def extract_frame():
    # Check if video file is present in the request
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    video_file = request.files['video']
    
    # Check if the file is empty
    if video_file.filename == '':
        return jsonify({'error': 'No video file selected'}), 400
    
    # Get frame number from request
    try:
        frame_number = int(request.form.get('frameNumber', 0))
        if frame_number < 0:
            return jsonify({'error': 'Frame number must be a positive integer'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid frame number'}), 400
        
    # Get video file name (optional)
    video_file_name = request.form.get('videoFileName', '')
    if video_file_name:
        video_file_name = sanitize_filename(video_file_name)
    
    # Check if the file extension is allowed
    if not allowed_file(video_file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Create temporary directory to store files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Generate unique filenames
        temp_video_path = os.path.join(temp_dir, f"{uuid.uuid4()}.mp4")
        temp_frame_path = os.path.join(temp_dir, f"{uuid.uuid4()}.png")
        
        # Save the uploaded video to the temporary directory
        video_file.save(temp_video_path)
        
        # Use ffmpeg to extract the frame
        try:
            # Command to extract a specific frame at the given second
            cmd = [
                'ffmpeg',
                '-i', temp_video_path,
                '-ss', str(frame_number),  # Seek to the specified second
                '-frames:v', '1',          # Extract only one frame
                '-q:v', '2',               # High quality
                temp_frame_path,
                '-y'                       # Overwrite output file if it exists
            ]
            
            # Run the ffmpeg command
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False
            )
            
            # Check if the frame was successfully extracted
            if process.returncode != 0 or not os.path.exists(temp_frame_path) or os.path.getsize(temp_frame_path) == 0:
                error_msg = f"Frame at second {frame_number} could not be found."
                return jsonify({'error': error_msg}), 404
            
            # Return the extracted frame
            output_filename = f"frame_{frame_number}.png"
            if video_file_name:
                # Use the original video filename as part of the output filename
                base_name = os.path.splitext(video_file_name)[0]
                output_filename = f"{base_name}_frame_{frame_number}.png"
                
            return send_file(
                temp_frame_path,
                mimetype='image/png',
                as_attachment=True,
                download_name=output_filename
            )
            
        except Exception as e:
            return jsonify({'error': f'Error processing video: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)