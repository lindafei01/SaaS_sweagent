
#!/usr/bin/env python3
import os
import tempfile
import subprocess
from flask import Flask, request, send_file, jsonify
import uuid

app = Flask(__name__)

# Maximum number of files allowed to be uploaded at once
MAX_FILES = 20

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    """Check if the file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/concatenate', methods=['POST'])
def concatenate_pdfs():
    # Check if files were uploaded
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    
    # Check if any files were selected
    if not files or len(files) == 0 or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    # Check if too many files were uploaded
    if len(files) > MAX_FILES:
        return jsonify({'error': f'Too many files. Maximum allowed is {MAX_FILES}'}), 400
    
    # Check if all files are PDFs
    for file in files:
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
    
    try:
        # Create a temporary directory to store the uploaded files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded files to the temporary directory
            file_paths = []
            for file in files:
                # Generate a secure filename
                secure_filename = str(uuid.uuid4()) + '.pdf'
                file_path = os.path.join(temp_dir, secure_filename)
                file.save(file_path)
                file_paths.append(file_path)
            
            # Create output file path
            output_path = os.path.join(temp_dir, 'concatenated.pdf')
            
            # Use pdfunite to concatenate the PDFs
            cmd = ['pdfunite'] + file_paths + [output_path]
            process = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            # Check if the command was successful
            if process.returncode != 0:
                app.logger.error(f"pdfunite error: {process.stderr}")
                return jsonify({'error': 'An error occurred while processing the files'}), 500
            
            # Return the concatenated PDF
            return send_file(
                output_path,
                mimetype='application/pdf',
                as_attachment=True,
                download_name='concatenated.pdf'
            )
    
    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify({'error': 'An error occurred while processing the files'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)