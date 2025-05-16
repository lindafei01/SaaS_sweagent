
import json
from django.test import TestCase, Client
from django.urls import reverse
from .models import Service


class ServiceMonitoringTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.heartbeat_url = reverse('heartbeat')
        self.services_url = reverse('services')
        
    def test_heartbeat_endpoint(self):
        # Test successful heartbeat
        data = {
            'serviceId': 'test-service',
            'token': 'test-token'
        }
        response = self.client.post(
            self.heartbeat_url,
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify service was created
        service = Service.objects.get(service_id='test-service')
        self.assertEqual(service.token, 'test-token')
        
        # Test missing fields
        data = {'serviceId': 'test-service'}
        response = self.client.post(
            self.heartbeat_url,
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
    def test_services_endpoint(self):
        # Create test services
        Service.objects.create(service_id='service1', token='token1')
        Service.objects.create(service_id='service2', token='token1')
        Service.objects.create(service_id='service3', token='token2')
        
        # Test retrieving services with token1
        data = {'token': 'token1'}
        response = self.client.post(
            self.services_url,
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 2)
        service_ids = [s['serviceId'] for s in response_data]
        self.assertIn('service1', service_ids)
        self.assertIn('service2', service_ids)
        self.assertNotIn('service3', service_ids)
        
        # Test retrieving services with token2
        data = {'token': 'token2'}
        response = self.client.post(
            self.services_url,
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['serviceId'], 'service3')