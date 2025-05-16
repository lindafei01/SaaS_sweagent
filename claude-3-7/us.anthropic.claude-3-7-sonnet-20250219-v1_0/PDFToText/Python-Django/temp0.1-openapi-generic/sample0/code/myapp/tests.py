
from django.test import TestCase, Client
from django.urls import reverse
import os
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile

# Create your tests here.
class PDFToTextTests(TestCase):
    def test_convert_endpoint_no_file(self):
        """Test the convert endpoint with no file"""
        client = Client()
        response = client.post('/convert')
        self.assertEqual(response.status_code, 400)
    
    def test_convert_endpoint_invalid_file(self):
        """Test the convert endpoint with an invalid file"""
        client = Client()
        with tempfile.NamedTemporaryFile(suffix='.txt') as temp:
            temp.write(b'This is not a PDF file')
            temp.seek(0)
            response = client.post('/convert', {'file': SimpleUploadedFile(temp.name, temp.read())})
            self.assertEqual(response.status_code, 400)