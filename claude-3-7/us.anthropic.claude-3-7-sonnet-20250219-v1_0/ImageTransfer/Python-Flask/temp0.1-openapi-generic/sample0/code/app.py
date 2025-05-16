
#!/usr/bin/env python3
import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)

# Security headers
@app.after_request
def add_security_headers(response):
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    # Enable XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# Configuration
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

@app.route('/', methods=['GET'])
def index():
    """Provide basic information about the API."""
    return jsonify({
        'title': 'Image Upload and Share API',
        'version': '1.0.0',
        'description': 'An API for uploading images and generating shareable links.',
        'endpoints': {
            '/upload': 'POST - Upload an image',
            '/images/{imageId}': 'GET - View an image'
        }
    })

# Helper function to check if file has an extension
def allowed_file(filename):
    # Accept all formats as per the OpenAPI schema
    return '.' in filename

@app.route('/upload', methods=['POST'])
def upload_image():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    
    # If user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Basic MIME type validation to ensure it's an image
        content_type = file.content_type
        if not content_type or not content_type.startswith('image/'):
            return jsonify({'error': 'File must be an image'}), 400
            
        # Generate a unique ID for the image
        image_id = str(uuid.uuid4())
        
        # Get the file extension
        filename = secure_filename(file.filename)
        extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        # Save the file with the unique ID as the filename
        if extension:
            filename = f"{image_id}.{extension}"
        else:
            filename = image_id
            
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            file.save(file_path)
            return jsonify({'id': image_id}), 200
        except Exception as e:
            app.logger.error(f"Error saving file: {str(e)}")
            return jsonify({'error': 'Failed to save file'}), 500
    else:
        return jsonify({'error': 'Invalid file format'}), 400

@app.route('/images/<image_id>', methods=['GET'])
def get_image(image_id):
    # Sanitize the image_id to prevent directory traversal attacks
    image_id = secure_filename(image_id)
    
    try:
        # Look for the file with the given ID in the upload folder
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if filename.startswith(image_id + '.') or filename == image_id:
                # Get the file's mimetype based on extension
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Return the file with its original mimetype
                # Add Content-Disposition header to ensure image is viewed in browser
                return send_from_directory(app.config['UPLOAD_FOLDER'], filename, 
                                          as_attachment=False)
        
        # If no matching file is found
        return jsonify({'error': 'Image not found'}), 404
    except Exception as e:
        app.logger.error(f"Error retrieving image: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large'}), 413

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)