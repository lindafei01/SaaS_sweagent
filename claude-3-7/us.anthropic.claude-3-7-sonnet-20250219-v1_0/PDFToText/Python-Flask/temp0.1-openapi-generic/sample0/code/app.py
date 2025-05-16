
#!/usr/bin/env python3
"""
PDF to Text Converter API

A simple Flask API to convert PDF files to Text format using pdftotext utility.
"""

import os
import subprocess
import tempfile
from flask import Flask, request, jsonify, make_response
import werkzeug.utils

# Initialize Flask app
app = Flask(__name__)

# Maximum allowed file size (10MB)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_pdf_to_text(pdf_path):
    """Convert PDF to text using pdftotext utility"""
    try:
        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_txt:
            temp_txt_path = temp_txt.name
        
        # Run pdftotext command
        process = subprocess.run(
            ['pdftotext', pdf_path, temp_txt_path],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Read the text content
        with open(temp_txt_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        # Clean up temporary file
        os.unlink(temp_txt_path)
        
        return text_content, None
    except subprocess.CalledProcessError as e:
        return None, f"PDF conversion failed: {e.stderr}"
    except Exception as e:
        return None, f"Error processing PDF: {str(e)}"

@app.route('/convert', methods=['POST'])
def convert_pdf():
    """Endpoint to convert PDF to text"""
    # Check if file part exists in request
    if 'file' not in request.files:
        return make_response(jsonify({'error': 'No file part in the request'}), 400)
    
    file = request.files['file']
    
    # Check if file is selected
    if file.filename == '':
        return make_response(jsonify({'error': 'No file selected'}), 400)
    
    # Check if file extension is allowed
    if not allowed_file(file.filename):
        return make_response(jsonify({'error': 'File type not allowed. Only PDF files are accepted'}), 400)
    
    try:
        # Save the file temporarily
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name
            file.save(temp_pdf_path)
        
        # Convert PDF to text
        text_content, error = convert_pdf_to_text(temp_pdf_path)
        
        # Clean up temporary file
        os.unlink(temp_pdf_path)
        
        if error:
            return make_response(jsonify({'error': error}), 500)
        
        # Return the text content
        response = make_response(text_content)
        response.headers['Content-Type'] = 'text/plain'
        return response
    
    except Exception as e:
        return make_response(jsonify({'error': f'Internal server error: {str(e)}'}), 500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)