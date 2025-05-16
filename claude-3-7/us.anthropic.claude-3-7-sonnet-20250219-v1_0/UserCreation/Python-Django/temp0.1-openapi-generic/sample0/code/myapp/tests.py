
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Invitation

class InvitationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_invite_user(self):
        response = self.client.post(
            reverse('invite_user'),
            json.dumps({'email': 'test@example.com'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('invite_id', data)
        self.assertIn('message', data)
        
        # Test duplicate invitation
        response = self.client.post(
            reverse('invite_user'),
            json.dumps({'email': 'test@example.com'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('invite_id', data)
        self.assertEqual(data['message'], 'Invitation already exists')
    
    def test_create_user(self):
        # Create an invitation first
        response = self.client.post(
            reverse('invite_user'),
            json.dumps({'email': 'newuser@example.com'}),
            content_type='application/json'
        )
        invite_id = json.loads(response.content)['invite_id']
        
        # Test user creation with valid invite_id
        response = self.client.post(
            reverse('create_user'),
            json.dumps({
                'invite_id': invite_id,
                'user_name': 'newuser',
                'password': 'newpassword'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Test with invalid invite_id
        response = self.client.post(
            reverse('create_user'),
            json.dumps({
                'invite_id': '00000000-0000-0000-0000-000000000000',
                'user_name': 'anotheruser',
                'password': 'password'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
        
        # Test with duplicate username
        response = self.client.post(
            reverse('invite_user'),
            json.dumps({'email': 'another@example.com'}),
            content_type='application/json'
        )
        invite_id = json.loads(response.content)['invite_id']
        
        response = self.client.post(
            reverse('create_user'),
            json.dumps({
                'invite_id': invite_id,
                'user_name': 'newuser',  # Already exists
                'password': 'password'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)