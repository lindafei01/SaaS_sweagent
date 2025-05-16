
import zipfile
import io
import requests
import sys

def create_test_zip():
    """Create a test zip file with some text files"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        zip_file.writestr('file1.txt', 'Hello ')
        zip_file.writestr('file2.txt', 'World!')
        zip_file.writestr('file3.txt', '\nThis is a test.')
    
    return zip_buffer.getvalue()

def test_conversion():
    """Test the zip to text conversion API"""
    zip_data = create_test_zip()
    
    # Send the zip file to the API
    files = {'file': ('test.zip', zip_data, 'application/zip')}
    response = requests.post('http://localhost:5000/convert', files=files)
    
    # Print the response
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print("Conversion successful!")
        print("Response content:")
        print(response.text)
    else:
        print("Conversion failed!")
        print(f"Error: {response.text}")
        sys.exit(1)

if __name__ == "__main__":
    print("Testing zip to text conversion API...")
    test_conversion()
    print("Test completed successfully!")