
from django.test import TestCase, Client
from django.urls import reverse
import zipfile
import io
import tempfile

# Create your tests here.
class ZipToTextConversionTest(TestCase):
    def test_convert_endpoint(self):
        # Create a test zip file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            zip_file.writestr('file1.txt', 'Hello')
            zip_file.writestr('file2.txt', 'World')
        
        zip_buffer.seek(0)
        
        # Create a temporary file to simulate file upload
        with tempfile.NamedTemporaryFile(suffix='.zip') as temp_file:
            temp_file.write(zip_buffer.getvalue())
            temp_file.flush()
            
            # Open the file for reading
            with open(temp_file.name, 'rb') as file:
                # Send POST request to the convert endpoint
                response = self.client.post(
                    '/convert',
                    {'file': file},
                    format='multipart'
                )
                
                # Check response status code
                self.assertEqual(response.status_code, 200)
                
                # Check response content
                self.assertEqual(response.content.decode(), 'HelloWorld')
    
    def test_invalid_file(self):
        # Test with a non-zip file
        with tempfile.NamedTemporaryFile(suffix='.txt') as temp_file:
            temp_file.write(b'This is not a zip file')
            temp_file.flush()
            
            with open(temp_file.name, 'rb') as file:
                response = self.client.post(
                    '/convert',
                    {'file': file},
                    format='multipart'
                )
                
                # Check response status code for invalid input
                self.assertEqual(response.status_code, 400)