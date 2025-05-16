
import json
import os
from django.test import TestCase, Client
from django.conf import settings

class LoggingAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Ensure we're using a test log file
        settings.LOG_FILE_PATH = os.path.join(settings.BASE_DIR, 'test_logs.txt')
        # Clear the test log file if it exists
        if os.path.exists(settings.LOG_FILE_PATH):
            os.remove(settings.LOG_FILE_PATH)

    def tearDown(self):
        # Clean up the test log file
        if os.path.exists(settings.LOG_FILE_PATH):
            os.remove(settings.LOG_FILE_PATH)

    def test_log_message(self):
        # Test posting a log message
        response = self.client.post(
            '/log',
            json.dumps({'message': 'Test log message'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'success'})

        # Verify the message was written to the log file
        with open(settings.LOG_FILE_PATH, 'r') as f:
            log_content = f.read()
        self.assertIn('Test log message', log_content)

    def test_get_logs(self):
        # First add a log message
        self.client.post(
            '/log',
            json.dumps({'message': 'Test log message'}),
            content_type='application/json'
        )

        # Test getting all logs
        response = self.client.get('/logs')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test log message', response.content.decode('utf-8'))

    def test_log_message_missing_message(self):
        # Test posting without a message
        response = self.client.post(
            '/log',
            json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'Message is required'})