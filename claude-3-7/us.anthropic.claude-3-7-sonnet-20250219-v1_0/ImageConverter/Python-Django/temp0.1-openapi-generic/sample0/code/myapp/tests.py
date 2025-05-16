
from django.test import TestCase, Client
from django.urls import reverse
import os
import tempfile
from PIL import Image
import io

# Create your tests here.
class GifCreatorTests(TestCase):
    def setUp(self):
        self.client = Client()
        
    def create_test_image(self):
        # Create a simple test image
        image = Image.new('RGB', (100, 100), color='red')
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(temp_file.name)
        temp_file.seek(0)
        return temp_file
        
    def test_create_gif_endpoint(self):
        # Create test images
        img1 = self.create_test_image()
        img2 = self.create_test_image()
        
        # Test valid request
        with open(img1.name, 'rb') as img1_file, open(img2.name, 'rb') as img2_file:
            response = self.client.post(reverse('create_gif'), {
                'images': [img1_file, img2_file],
                'targetSize': '100x100',
                'delay': 100,
                'appendReverted': True
            }, format='multipart')
            
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/gif')
        
        # Test invalid request - missing required field
        with open(img1.name, 'rb') as img1_file:
            response = self.client.post(reverse('create_gif'), {
                'images': [img1_file],
                # Missing targetSize
                'delay': 100
            }, format='multipart')
            
        self.assertEqual(response.status_code, 400)
        
        # Clean up
        img1.close()
        img2.close()