
#!/usr/bin/env python3
from flask import Flask, request, jsonify
import os
import tempfile
import subprocess
import re
import shutil

app = Flask(__name__)

def sanitize_filename(filename):
    """Sanitize the filename to prevent path traversal attacks."""
    return os.path.basename(filename)

def compile_typescript(file_content, filename):
    """
    Compile TypeScript code and return compilation result.
    
    Args:
        file_content (str): The TypeScript code to compile
        filename (str): The name of the file
    
    Returns:
        tuple: (has_error, compiler_error)
    """
    # Create a temporary directory to store the file
    with tempfile.TemporaryDirectory() as temp_dir:
        # Sanitize the filename
        safe_filename = sanitize_filename(filename)
        file_path = os.path.join(temp_dir, safe_filename)
        
        # Write the content to the file
        with open(file_path, 'w') as f:
            f.write(file_content)
        
        try:
            # Run the TypeScript compiler
            result = subprocess.run(
                ['tsc', '--noEmit', file_path],
                capture_output=True,
                text=True
            )
            
            # Check if compilation was successful
            if result.returncode == 0:
                return False, None
            else:
                # Return the compiler error
                return True, result.stderr.strip()
        except FileNotFoundError:
            return True, "TypeScript compiler (tsc) not found. Please make sure it's installed."

def compile_cpp(file_content, filename):
    """
    Compile C++ code and return compilation result.
    
    Args:
        file_content (str): The C++ code to compile
        filename (str): The name of the file
    
    Returns:
        tuple: (has_error, compiler_error)
    """
    # Create a temporary directory to store the file
    with tempfile.TemporaryDirectory() as temp_dir:
        # Sanitize the filename
        safe_filename = sanitize_filename(filename)
        file_path = os.path.join(temp_dir, safe_filename)
        
        # Write the content to the file
        with open(file_path, 'w') as f:
            f.write(file_content)
        
        # Output file path
        output_path = os.path.join(temp_dir, 'output')
        
        try:
            # Run the C++ compiler
            result = subprocess.run(
                ['g++', '-o', output_path, file_path],
                capture_output=True,
                text=True
            )
            
            # Check if compilation was successful
            if result.returncode == 0:
                return False, None
            else:
                # Return the compiler error
                return True, result.stderr.strip()
        except FileNotFoundError:
            return True, "C++ compiler (g++) not found. Please make sure it's installed."

@app.route('/compile', methods=['POST'])
def compile_code():
    """
    Endpoint to compile code and return the result.
    
    Expects a JSON payload with:
    - fileName: The name of the file
    - fileContent: The content of the file
    
    Returns:
    - hasError: Whether the compilation had errors
    - compilerError: The compiler error message, if any
    """
    # Get the request data
    data = request.get_json()
    
    # Validate the request data
    if not data or 'fileName' not in data or 'fileContent' not in data:
        return jsonify({
            'hasError': True,
            'compilerError': 'Invalid request. Missing fileName or fileContent.'
        }), 400
    
    file_name = data['fileName']
    file_content = data['fileContent']
    
    # Determine the file type and compile accordingly
    if file_name.endswith('.ts'):
        has_error, compiler_error = compile_typescript(file_content, file_name)
    elif file_name.endswith('.cpp'):
        has_error, compiler_error = compile_cpp(file_content, file_name)
    else:
        return jsonify({
            'hasError': True,
            'compilerError': 'Unsupported file type. Only .ts and .cpp files are supported.'
        }), 400
    
    # Return the compilation result
    return jsonify({
        'hasError': has_error,
        'compilerError': compiler_error
    })

if __name__ == '__main__':
    # Start the Flask server
    app.run(host='0.0.0.0', port=5000)