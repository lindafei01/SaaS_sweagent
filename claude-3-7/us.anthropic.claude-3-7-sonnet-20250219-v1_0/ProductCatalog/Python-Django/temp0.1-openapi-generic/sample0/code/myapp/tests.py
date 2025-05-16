
from django.test import TestCase, Client
from django.urls import reverse
import json
from .models import Product

class ProductAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.product_data = {
            'name': 'Test Product',
            'color': 'red',
            'size': 'large',
            'price': '100'
        }
    
    def test_add_product(self):
        response = self.client.post(
            reverse('add_product'),
            data=json.dumps(self.product_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Product.objects.filter(name='Test Product').exists())
    
    def test_search_product(self):
        # Add a product first
        self.client.post(
            reverse('add_product'),
            data=json.dumps(self.product_data),
            content_type='application/json'
        )
        
        # Search for the product
        response = self.client.get(reverse('search_products'), {'query': 'red'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['name'], 'Test Product')
    
    def test_download_product(self):
        # Add a product first
        self.client.post(
            reverse('add_product'),
            data=json.dumps(self.product_data),
            content_type='application/json'
        )
        
        # Download the product data
        response = self.client.get(reverse('download_product'), {'name': 'Test Product'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('data', data)
        
        # Parse the data
        product_properties = json.loads(data['data'])
        self.assertEqual(product_properties['color'], 'red')
        self.assertEqual(product_properties['size'], 'large')
    
    def test_upload_product(self):
        # Add a product first
        self.client.post(
            reverse('add_product'),
            data=json.dumps(self.product_data),
            content_type='application/json'
        )
        
        # Update the product data
        updated_data = {
            'name': 'Test Product',
            'data': json.dumps({
                'color': 'blue',
                'size': 'medium',
                'material': 'cotton'
            })
        }
        
        response = self.client.post(
            reverse('upload_product'),
            data=json.dumps(updated_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify the update
        product = Product.objects.get(name='Test Product')
        properties = product.get_properties()
        self.assertEqual(properties['color'], 'blue')
        self.assertEqual(properties['size'], 'medium')
        self.assertEqual(properties['material'], 'cotton')
        self.assertNotIn('price', properties)