
from django.test import TestCase, Client
from django.urls import reverse
from .models import UserProfile
import io
from PIL import Image

class UserProfileTests(TestCase):
    def setUp(self):
        # Create a test PNG image
        self.image_file = self._create_test_image()
        
    def _create_test_image(self):
        # Create a simple test PNG image
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), color='red')
        image.save(file, 'png')
        file.name = 'test.png'
        file.seek(0)
        return file
        
    def test_add_profile(self):
        # Test adding a new profile
        client = Client()
        response = client.post(reverse('add_profile'), {
            'username': 'testuser',
            'profile_page': '<html><body>Test Profile</body></html>',
            'profile_photo': self.image_file
        })
        self.assertEqual(response.status_code, 201)
        
        # Check that profile was created
        self.assertTrue(UserProfile.objects.filter(username='testuser').exists())
        
    def test_add_duplicate_profile(self):
        # Create a profile first
        UserProfile.objects.create(
            username='testuser',
            profile_page='<html><body>Test Profile</body></html>',
            profile_photo=self.image_file.read()
        )
        
        # Try to create the same profile again
        client = Client()
        self.image_file.seek(0)  # Reset file pointer
        response = client.post(reverse('add_profile'), {
            'username': 'testuser',
            'profile_page': '<html><body>Another Profile</body></html>',
            'profile_photo': self.image_file
        })
        self.assertEqual(response.status_code, 403)
        
    def test_get_profile(self):
        # Create a profile
        UserProfile.objects.create(
            username='testuser',
            profile_page='<html><body>Test Profile</body></html>',
            profile_photo=self.image_file.read()
        )
        
        # Get the profile
        client = Client()
        response = client.get(reverse('get_profile', args=['testuser']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), '<html><body>Test Profile</body></html>')
        
    def test_get_nonexistent_profile(self):
        client = Client()
        response = client.get(reverse('get_profile', args=['nonexistent']))
        self.assertEqual(response.status_code, 404)
        
    def test_get_profile_photo(self):
        # Create a profile
        photo_data = self.image_file.read()
        UserProfile.objects.create(
            username='testuser',
            profile_page='<html><body>Test Profile</body></html>',
            profile_photo=photo_data
        )
        
        # Get the profile photo
        client = Client()
        response = client.get(reverse('get_profile_photo', args=['testuser']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertEqual(response.content, photo_data)