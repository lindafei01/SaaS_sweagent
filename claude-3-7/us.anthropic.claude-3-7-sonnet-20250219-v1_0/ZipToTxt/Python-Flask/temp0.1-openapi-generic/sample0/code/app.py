
#!/usr/bin/env python3
import os
import io
import zipfile
from flask import Flask, request, Response
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Set maximum content length to 16MB to prevent DOS attacks
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

@app.route('/convert', methods=['POST'])
def convert_zip_to_text():
    """
    Convert a zip file to a text file.
    
    Takes a zip file as input and returns a text file containing the
    concatenated contents of all text files in the zip.
    """
    # Check if the post request has the file part
    if 'file' not in request.files:
        return Response("No file part in the request", status=400)
    
    file = request.files['file']
    
    # If user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return Response("No selected file", status=400)
    
    # Check if the file is a zip file
    if not file.filename.endswith('.zip'):
        return Response("File must be a zip file", status=400)
    
    try:
        # Create a BytesIO object from the file
        file_stream = io.BytesIO(file.read())
        
        # Check if it's a valid zip file
        if not zipfile.is_zipfile(file_stream):
            return Response("Invalid zip file", status=400)
        
        # Reset the file pointer to the beginning of the file
        file_stream.seek(0)
        
        # Open the zip file
        with zipfile.ZipFile(file_stream, 'r') as zip_ref:
            # Get all file names in the zip
            file_names = zip_ref.namelist()
            
            # Filter out directories and non-text files
            # This is a simple heuristic - in a real application, you might want to use
            # more sophisticated methods to determine if a file is text
            text_files = [name for name in file_names 
                         if not name.endswith('/') and is_likely_text_file(name)]
            
            if not text_files:
                return Response("No text files found in the zip", status=400)
            
            # Concatenate the contents of all text files
            combined_text = ""
            for text_file in text_files:
                try:
                    # Extract the file content
                    content = zip_ref.read(text_file).decode('utf-8')
                    # Add a header with the filename
                    combined_text += f"--- {text_file} ---\n{content}\n\n"
                except UnicodeDecodeError:
                    # Skip files that can't be decoded as UTF-8
                    continue
                except Exception as e:
                    # Log the error and continue with the next file
                    app.logger.error(f"Error processing {text_file}: {str(e)}")
                    continue
            
            if not combined_text:
                return Response("Could not extract any text content from the zip", status=400)
            
            # Return the combined text
            return Response(combined_text, mimetype='text/plain')
    
    except zipfile.BadZipFile:
        return Response("Invalid zip file format", status=400)
    except Exception as e:
        app.logger.error(f"Error processing zip file: {str(e)}")
        return Response("Error processing zip file", status=400)

def is_likely_text_file(filename):
    """
    Check if a file is likely to be a text file based on its extension.
    
    Args:
        filename: The name of the file to check
        
    Returns:
        bool: True if the file is likely to be a text file, False otherwise
    """
    text_extensions = {
        '.txt', '.csv', '.md', '.json', '.xml', '.html', '.htm', '.css', 
        '.js', '.py', '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.php',
        '.rb', '.pl', '.sh', '.bat', '.log', '.ini', '.cfg', '.conf',
        '.yaml', '.yml', '.toml', '.rst', '.tex', '.sql'
    }
    
    _, ext = os.path.splitext(filename.lower())
    return ext in text_extensions

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)