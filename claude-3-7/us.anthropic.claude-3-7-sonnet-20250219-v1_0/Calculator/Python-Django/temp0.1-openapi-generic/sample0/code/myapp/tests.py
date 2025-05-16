
import json
from django.test import TestCase, Client
from django.urls import reverse

class CalculatorTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.calculator_url = reverse('calculator')
    
    def test_valid_expression(self):
        """Test that a valid expression returns the correct result"""
        payload = {'expression': '1 + 2*3'}
        response = self.client.post(
            self.calculator_url,
            json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'result': '7'})
    
    def test_complex_expression(self):
        """Test a more complex expression"""
        payload = {'expression': '(10 + 5) * 2 - 8 / 4'}
        response = self.client.post(
            self.calculator_url,
            json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'result': '28.0'})
    
    def test_missing_expression(self):
        """Test that missing expression field returns 400"""
        payload = {'wrong_field': '1+1'}
        response = self.client.post(
            self.calculator_url,
            json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_invalid_json(self):
        """Test that invalid JSON returns 400"""
        response = self.client.post(
            self.calculator_url,
            '{invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_invalid_expression(self):
        """Test that invalid expression returns 400"""
        payload = {'expression': '1 + * 2'}
        response = self.client.post(
            self.calculator_url,
            json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_unsafe_expression(self):
        """Test that potentially unsafe expressions are rejected"""
        payload = {'expression': '__import__("os").system("ls")'}
        response = self.client.post(
            self.calculator_url,
            json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)