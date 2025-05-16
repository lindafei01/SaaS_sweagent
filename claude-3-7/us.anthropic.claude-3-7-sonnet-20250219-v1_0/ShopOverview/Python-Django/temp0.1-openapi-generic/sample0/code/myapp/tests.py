
from django.test import TestCase, Client
from django.urls import reverse
from .models import Merchant, Ware
import json

class MerchantTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register_merchant')
        self.login_url = reverse('login_merchant')
        self.upload_url = reverse('upload_wares')
        
    def test_register_merchant(self):
        data = {
            'email': 'test@example.com',
            'name': 'Test Merchant',
            'password': 'password123'
        }
        response = self.client.post(
            self.register_url,
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Merchant.objects.filter(email='test@example.com').exists())
        
    def test_login_merchant(self):
        # First register a merchant
        merchant_data = {
            'email': 'login@example.com',
            'name': 'Login Test',
            'password': 'password123'
        }
        self.client.post(
            self.register_url,
            json.dumps(merchant_data),
            content_type='application/json'
        )
        
        # Now try to login
        login_data = {
            'email': 'login@example.com',
            'password': 'password123'
        }
        response = self.client.post(
            self.login_url,
            json.dumps(login_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue('AUTH_COOKIE' in response.cookies)

class WareTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register_merchant')
        self.login_url = reverse('login_merchant')
        self.upload_url = reverse('upload_wares')
        self.wares_url = reverse('list_wares')
        
        # Create a merchant and login
        merchant_data = {
            'email': 'ware@example.com',
            'name': 'Ware Test',
            'password': 'password123'
        }
        self.client.post(
            self.register_url,
            json.dumps(merchant_data),
            content_type='application/json'
        )
        
        login_data = {
            'email': 'ware@example.com',
            'password': 'password123'
        }
        self.client.post(
            self.login_url,
            json.dumps(login_data),
            content_type='application/json'
        )
        
    def test_upload_wares(self):
        csv_data = "Product1,Description1,10.99\nProduct2,Description2,20.50"
        data = {'csv': csv_data}
        response = self.client.post(
            self.upload_url,
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Ware.objects.count(), 2)
        
    def test_list_wares(self):
        # First upload some wares
        csv_data = "Product1,Description1,10.99\nProduct2,Description2,20.50"
        data = {'csv': csv_data}
        self.client.post(
            self.upload_url,
            json.dumps(data),
            content_type='application/json'
        )
        
        # Now test listing wares
        response = self.client.get(self.wares_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Product1')
        self.assertContains(response, 'Product2')
        
        # Test with price filter
        response = self.client.get(f"{self.wares_url}?minPrice=15")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Product1')
        self.assertContains(response, 'Product2')