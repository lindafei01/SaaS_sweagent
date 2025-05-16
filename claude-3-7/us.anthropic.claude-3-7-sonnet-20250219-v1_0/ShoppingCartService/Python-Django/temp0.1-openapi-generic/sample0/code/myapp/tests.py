
import json
from django.test import TestCase, Client
from django.urls import reverse
from .models import Cart, CartItem

class ShoppingCartTests(TestCase):
    def setUp(self):
        self.client = Client()
        
    def test_create_cart(self):
        """Test creating a new cart."""
        response = self.client.post(reverse('create_cart'))
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertIn('cart_id', data)
        
    def test_add_to_cart(self):
        """Test adding an item to the cart."""
        # First create a cart
        response = self.client.post(reverse('create_cart'))
        cart_id = json.loads(response.content)['cart_id']
        
        # Add an item to the cart
        payload = {
            'cart_id': cart_id,
            'item_id': 1,
            'count': 3
        }
        response = self.client.post(
            reverse('add_to_cart'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify the item was added
        cart = Cart.objects.get(cart_id=cart_id)
        cart_item = CartItem.objects.get(cart=cart, item_id=1)
        self.assertEqual(cart_item.count, 3)
        
    def test_retrieve_cart(self):
        """Test retrieving items from the cart."""
        # First create a cart
        response = self.client.post(reverse('create_cart'))
        cart_id = json.loads(response.content)['cart_id']
        
        # Add items to the cart
        cart = Cart.objects.get(cart_id=cart_id)
        CartItem.objects.create(cart=cart, item_id=1, count=3)
        CartItem.objects.create(cart=cart, item_id=2, count=2)
        
        # Retrieve the cart
        payload = {'cart_id': cart_id}
        response = self.client.post(
            reverse('retrieve_cart'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify the response
        data = json.loads(response.content)
        self.assertIn('items', data)
        self.assertEqual(len(data['items']), 2)
        
        # Check that the items are correct
        items = {item['item_id']: item['count'] for item in data['items']}
        self.assertEqual(items[1], 3)
        self.assertEqual(items[2], 2)
        
    def test_remove_from_cart(self):
        """Test removing an item from the cart."""
        # First create a cart
        response = self.client.post(reverse('create_cart'))
        cart_id = json.loads(response.content)['cart_id']
        
        # Add an item to the cart
        cart = Cart.objects.get(cart_id=cart_id)
        CartItem.objects.create(cart=cart, item_id=1, count=3)
        
        # Remove the item
        payload = {
            'cart_id': cart_id,
            'item_id': 1,
            'count': -3  # Negative count to remove
        }
        response = self.client.post(
            reverse('add_to_cart'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify the item was removed
        self.assertEqual(CartItem.objects.filter(cart=cart, item_id=1).count(), 0)