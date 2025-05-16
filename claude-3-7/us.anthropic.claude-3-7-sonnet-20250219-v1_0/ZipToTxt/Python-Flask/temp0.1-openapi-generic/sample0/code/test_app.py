
#!/usr/bin/env python3
import os
import io
import zipfile
import requests
import tempfile

def create_test_zip():
    """Create a test zip file with some text files."""
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix='.zip')
    os.close(fd)
    
    # Create a zip file with some text files
    with zipfile.ZipFile(path, 'w') as zip_file:
        # Add a text file
        zip_file.writestr('file1.txt', 'This is the content of file 1.\n')
        # Add another text file
        zip_file.writestr('file2.txt', 'This is the content of file 2.\n')
        # Add a non-text file (binary data)
        zip_file.writestr('binary.bin', b'\x00\x01\x02\x03')
        # Add a text file in a subdirectory
        zip_file.writestr('subdir/file3.txt', 'This is the content of file 3.\n')
    
    return path

def test_convert_endpoint():
    """Test the /convert endpoint."""
    # Create a test zip file
    zip_path = create_test_zip()
    
    try:
        # Send the zip file to the API
        with open(zip_path, 'rb') as f:
            files = {'file': ('test.zip', f)}
            response = requests.post('http://0.0.0.0:5000/convert', files=files)
        
        # Check the response
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("Response content:")
            print(response.text)
        else:
            print(f"Error: {response.text}")
    finally:
        # Clean up
        os.unlink(zip_path)

if __name__ == '__main__':
    test_convert_endpoint()