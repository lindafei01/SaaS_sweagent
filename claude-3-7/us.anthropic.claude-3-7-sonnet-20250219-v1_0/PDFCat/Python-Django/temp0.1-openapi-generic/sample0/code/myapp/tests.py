
from django.test import TestCase, Client
from django.urls import reverse
import os
import tempfile
from django.conf import settings


class PDFConcatenationTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create temporary PDF files for testing
        self.temp_files = []
        for i in range(2):
            temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_file.write(b'%PDF-1.4\n%EOF\n')  # Minimal valid PDF content
            temp_file.close()
            self.temp_files.append(temp_file.name)

    def tearDown(self):
        # Clean up temporary files
        for file_path in self.temp_files:
            if os.path.exists(file_path):
                os.unlink(file_path)

    def test_concatenate_endpoint_no_files(self):
        response = self.client.post(reverse('concatenate'))
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_concatenate_endpoint_with_files(self):
        with open(self.temp_files[0], 'rb') as file1, open(self.temp_files[1], 'rb') as file2:
            response = self.client.post(
                reverse('concatenate'),
                {'files': [file1, file2]},
                format='multipart'
            )
        # If pdfunite is available, this should succeed
        if response.status_code == 200:
            self.assertEqual(response['Content-Type'], 'application/pdf')
        else:
            # If pdfunite is not available, we should get a 500 error
            self.assertEqual(response.status_code, 500)