
from django.test import TestCase, Client
from django.urls import reverse
import json
import os
import tempfile


class FileSearchTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create temporary test files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a test file with content
        with open(os.path.join(self.temp_dir.name, 'test_file.txt'), 'w') as f:
            f.write('hello world')
            
        # Create a nested directory with a test file
        os.makedirs(os.path.join(self.temp_dir.name, 'nested'))
        with open(os.path.join(self.temp_dir.name, 'nested', 'nested_file.txt'), 'w') as f:
            f.write('hello you')
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_search_endpoint_basic(self):
        # This test would need to be adjusted to use the actual files directory
        # For now, we'll just test the API response structure
        response = self.client.get(reverse('search'), {'regex': 'hello'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('files', data)
        self.assertIsInstance(data['files'], list)
    
    def test_search_invalid_regex(self):
        response = self.client.get(reverse('search'), {'regex': '['})  # Invalid regex
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)