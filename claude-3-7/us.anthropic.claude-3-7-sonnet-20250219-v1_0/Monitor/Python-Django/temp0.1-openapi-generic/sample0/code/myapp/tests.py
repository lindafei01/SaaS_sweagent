
from django.test import TestCase, Client
from django.urls import reverse
import json

# Create your tests here.
class MonitorCommandsTestCase(TestCase):
    def test_monitor_commands_endpoint(self):
        """Test that the monitor commands endpoint works correctly"""
        client = Client()
        url = reverse('monitor_commands')
        
        # Test with a valid request
        data = {
            'command_regex': 'python.*'
        }
        response = client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Check that the response is a list
        response_data = json.loads(response.content)
        self.assertIsInstance(response_data, list)
        
        # Test with missing required field
        data = {}
        response = client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)