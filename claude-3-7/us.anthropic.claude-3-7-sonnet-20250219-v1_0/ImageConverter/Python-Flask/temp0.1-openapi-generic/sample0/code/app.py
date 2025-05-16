
#!/usr/bin/env python3
import os
import re
import tempfile
import subprocess
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure maximum content length (100MB)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# Ensure the temp directory exists
TEMP_DIR = tempfile.gettempdir()

def validate_target_size(target_size):
    """Validate the target size format (e.g., '500x500')"""
    if not re.match(r'^\d+x\d+$', target_size):
        return False
    return True

def validate_delay(delay):
    """Validate the delay is a positive integer"""
    try:
        delay_val = int(delay)
        return delay_val > 0
    except (ValueError, TypeError):
        return False

def validate_image_file(file):
    """Basic validation for image files"""
    # Check if the file has an allowed extension
    allowed_extensions = {'png', 'jpg', 'jpeg', 'bmp', 'gif', 'webp'}
    filename = file.filename.lower()
    return '.' in filename and filename.rsplit('.', 1)[1] in allowed_extensions

def create_gif(image_paths, target_size, delay, append_reverted):
    """Create a GIF from the provided images using ImageMagick"""
    output_path = os.path.join(TEMP_DIR, 'output.gif')
    
    # Build the command for ImageMagick
    cmd = ['convert']
    
    # Add resize option
    cmd.append('-resize')
    cmd.append(target_size)
    
    # Add delay option (convert from milliseconds to centiseconds for ImageMagick)
    delay_cs = max(1, int(delay) // 10)  # Ensure minimum delay of 1 centisecond
    cmd.append('-delay')
    cmd.append(str(delay_cs))
    
    # Add all image paths
    cmd.extend(image_paths)
    
    # If append_reverted is True, add the images in reverse order (excluding the last one)
    if append_reverted and len(image_paths) > 1:
        cmd.extend(image_paths[-2::-1])
    
    # Output path
    cmd.append(output_path)
    
    try:
        # Run the command
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
    except subprocess.CalledProcessError as e:
        app.logger.error(f"Error creating GIF: {e.stderr.decode() if e.stderr else str(e)}")
        raise RuntimeError("Failed to create GIF")

@app.route('/create-gif', methods=['POST'])
def create_gif_endpoint():
    # Check if images were uploaded
    if 'images' not in request.files:
        return jsonify({'error': 'No images provided'}), 400
    
    # Get images
    images = request.files.getlist('images')
    if not images or len(images) == 0:
        return jsonify({'error': 'No images provided'}), 400
    
    # Validate images
    for image in images:
        if not validate_image_file(image):
            return jsonify({'error': f'Invalid image file: {image.filename}'}), 400
    
    # Get and validate target size
    target_size = request.form.get('targetSize')
    if not target_size or not validate_target_size(target_size):
        return jsonify({'error': 'Invalid or missing targetSize parameter (format should be WIDTHxHEIGHT)'}), 400
    
    # Get and validate delay
    delay = request.form.get('delay', '10')
    if not validate_delay(delay):
        return jsonify({'error': 'Invalid delay parameter (must be a positive integer)'}), 400
    
    # Get append_reverted flag
    append_reverted = request.form.get('appendReverted', 'false').lower() in ('true', '1', 't', 'yes')
    
    # Save uploaded images to temporary files
    temp_image_paths = []
    try:
        for image in images:
            # Secure the filename to prevent directory traversal attacks
            filename = secure_filename(image.filename)
            temp_path = os.path.join(TEMP_DIR, filename)
            image.save(temp_path)
            temp_image_paths.append(temp_path)
        
        # Create the GIF
        output_path = create_gif(temp_image_paths, target_size, delay, append_reverted)
        
        # Return the GIF file
        return send_file(output_path, mimetype='image/gif')
    
    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    
    finally:
        # Clean up temporary files
        for path in temp_image_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                app.logger.error(f"Error removing temporary file {path}: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)