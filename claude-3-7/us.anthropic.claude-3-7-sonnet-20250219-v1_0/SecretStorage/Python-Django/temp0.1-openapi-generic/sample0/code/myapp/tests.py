
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Secret
import json

class SecretStorageTestCase(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create a secret for the test user
        self.secret = Secret.objects.create(
            user=self.user,
            secret_text='test secret'
        )
    
    def test_register(self):
        """Test user registration"""
        url = reverse('register')
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'newpassword'
        }
        response = self.client.post(
            url, 
            json.dumps(data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_login(self):
        """Test user login"""
        url = reverse('login')
        data = {
            'email': 'test@example.com',
            'password': 'testpassword'
        }
        response = self.client.post(
            url, 
            json.dumps(data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.json())
    
    def test_set_secret(self):
        """Test setting a secret"""
        # First login to get token
        login_url = reverse('login')
        login_data = {
            'email': 'test@example.com',
            'password': 'testpassword'
        }
        login_response = self.client.post(
            login_url, 
            json.dumps(login_data), 
            content_type='application/json'
        )
        token = login_response.json()['token']
        
        # Now set a secret
        url = reverse('set_secret')
        data = {
            'username': 'testuser',
            'secret': 'new secret'
        }
        response = self.client.post(
            url, 
            json.dumps(data), 
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 200)
        
        # Check if secret was updated
        secret = Secret.objects.get(user=self.user)
        self.assertEqual(secret.secret_text, 'new secret')
    
    def test_get_secret(self):
        """Test getting a secret"""
        # First login to get token
        login_url = reverse('login')
        login_data = {
            'email': 'test@example.com',
            'password': 'testpassword'
        }
        login_response = self.client.post(
            login_url, 
            json.dumps(login_data), 
            content_type='application/json'
        )
        token = login_response.json()['token']
        
        # Now get the secret
        url = f"{reverse('get_secret')}?username=testuser"
        response = self.client.get(
            url,
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['secret'], 'test secret')