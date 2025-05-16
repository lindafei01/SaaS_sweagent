
from django.test import TestCase, Client
from django.urls import reverse
import json
from .models import Product, Tag

class RecommenderTestCase(TestCase):
    def setUp(self):
        # Create test products and tags
        self.product1 = Product.objects.create(name="Test Product 1")
        self.product2 = Product.objects.create(name="Test Product 2")
        
        self.tag1 = Tag.objects.create(name="tag1")
        self.tag2 = Tag.objects.create(name="tag2")
        
        self.tag1.products.add(self.product1)
        self.tag2.products.add(self.product2)
        
        self.client = Client()
    
    def test_get_recommendations(self):
        # Test GET request with tags
        response = self.client.get(reverse('recommender') + '?tags=tag1')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product 1")
        self.assertNotContains(response, "Test Product 2")
        
        # Test with multiple tags
        response = self.client.get(reverse('recommender') + '?tags=tag1,tag2')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product 1")
        self.assertContains(response, "Test Product 2")
    
    def test_post_product(self):
        # Test POST request to create a new product
        data = {
            'product_name': 'New Test Product',
            'tags': ['tag3', 'tag4']
        }
        response = self.client.post(
            reverse('recommender'),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify the product was created
        self.assertTrue(Product.objects.filter(name='New Test Product').exists())
        
        # Verify tags were created and associated
        self.assertTrue(Tag.objects.filter(name='tag3').exists())
        self.assertTrue(Tag.objects.filter(name='tag4').exists())
        
        # Verify the product has the correct tags
        product = Product.objects.get(name='New Test Product')
        self.assertEqual(product.tags.count(), 2)
        self.assertIn('tag3', [tag.name for tag in product.tags.all()])
        self.assertIn('tag4', [tag.name for tag in product.tags.all()])