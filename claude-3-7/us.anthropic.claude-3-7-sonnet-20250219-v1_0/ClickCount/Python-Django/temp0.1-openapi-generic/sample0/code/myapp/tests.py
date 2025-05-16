
from django.test import TestCase, Client
from django.urls import reverse
from .models import Click
from django.utils import timezone
from datetime import datetime, timedelta
import json

class ClickAPITestCase(TestCase):
    def setUp(self):
        # Create some test clicks with different timestamps
        self.today = timezone.now()
        self.yesterday = self.today - timedelta(days=1)
        self.tomorrow = self.today + timedelta(days=1)
        
        # Create test clicks with specific timestamps
        Click.objects.create(timestamp=self.yesterday)
        Click.objects.create(timestamp=self.today)
        Click.objects.create(timestamp=self.tomorrow)
        
        self.client = Client()
    
    def test_register_click(self):
        """Test that a click can be registered"""
        initial_count = Click.objects.count()
        response = self.client.post(reverse('register_click'))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Click.objects.count(), initial_count + 1)
    
    def test_retrieve_clicks_before(self):
        """Test retrieving clicks before a date"""
        # Use tomorrow's date to ensure we have clicks before it
        date_str = (self.today + timedelta(days=2)).strftime('%Y-%m-%d')
        response = self.client.get(f"{reverse('retrieve_clicks')}?date={date_str}&direction=<")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(len(data) >= 3)  # Should get all clicks (today, yesterday, and any auto-created)
    
    def test_retrieve_clicks_after(self):
        """Test retrieving clicks after a date"""
        # Use yesterday's date to ensure we have clicks after it
        date_str = (self.today - timedelta(days=2)).strftime('%Y-%m-%d')
        response = self.client.get(f"{reverse('retrieve_clicks')}?date={date_str}&direction=>")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(len(data) >= 3)  # Should get all clicks (today, tomorrow, and any auto-created)
    
    def test_retrieve_clicks_invalid_params(self):
        """Test retrieving clicks with invalid parameters"""
        # Missing direction
        response = self.client.get(f"{reverse('retrieve_clicks')}?date=2022-01-01")
        self.assertEqual(response.status_code, 400)
        
        # Missing date
        response = self.client.get(f"{reverse('retrieve_clicks')}?direction=>")
        self.assertEqual(response.status_code, 400)
        
        # Invalid direction
        response = self.client.get(f"{reverse('retrieve_clicks')}?date=2022-01-01&direction=invalid")
        self.assertEqual(response.status_code, 400)
        
        # Invalid date format
        response = self.client.get(f"{reverse('retrieve_clicks')}?date=not-a-date&direction=>")
        self.assertEqual(response.status_code, 400)