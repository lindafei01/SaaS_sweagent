
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import json
import os
from .models import Image

class ImageUploadTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
    def test_upload_image(self):
        # Create a test image
        image_content = b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        image = SimpleUploadedFile(
            name='test_image.gif',
            content=image_content,
            content_type='image/gif'
        )
        
        # Test upload endpoint
        response = self.client.post(reverse('upload_image'), {'file': image})
        self.assertEqual(response.status_code, 200)
        
        # Check if response contains image ID
        content = json.loads(response.content)
        self.assertIn('id', content)
        
        # Test if image was saved to database
        image_id = content['id']
        self.assertTrue(Image.objects.filter(id=image_id).exists())
        
        # Test get image endpoint
        response = self.client.get(reverse('get_image', args=[image_id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/gif')
        
    def test_upload_no_file(self):
        # Test upload with no file
        response = self.client.post(reverse('upload_image'), {})
        self.assertEqual(response.status_code, 400)
        
    def test_get_nonexistent_image(self):
        # Test getting a non-existent image
        response = self.client.get(reverse('get_image', args=['00000000-0000-0000-0000-000000000000']))
        self.assertEqual(response.status_code, 404)