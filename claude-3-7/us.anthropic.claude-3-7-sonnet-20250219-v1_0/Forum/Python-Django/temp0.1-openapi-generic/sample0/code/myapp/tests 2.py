
import json
from django.test import TestCase, Client
from django.urls import reverse
from .models import Message

class MessageTests(TestCase):
    def setUp(self):
        # Create test messages
        Message.objects.create(username="user1", content="Test message 1")
        Message.objects.create(username="user2", content="Test message 2")
        Message.objects.create(username="user3", content="Test message 3")
        
    def test_get_messages(self):
        client = Client()
        response = client.get('/messages')
        self.assertEqual(response.status_code, 200)
        
    def test_get_messages_with_params(self):
        client = Client()
        response = client.get('/messages?limit=2&offset=1&sort=ASC')
        self.assertEqual(response.status_code, 200)
        
    def test_post_message(self):
        client = Client()
        data = {
            'username': 'testuser',
            'content': 'This is a test message'
        }
        response = client.post(
            '/messages',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Check if message was created
        self.assertTrue(Message.objects.filter(username='testuser').exists())
        
    def test_post_invalid_message(self):
        client = Client()
        data = {
            'username': 'testuser'
            # Missing content field
        }
        response = client.post(
            '/messages',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)