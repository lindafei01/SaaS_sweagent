
import json
from django.test import TestCase, Client
from django.urls import reverse
from .models import CreditCard, PhoneNumber

class CreditCardAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        
    def test_associate_card(self):
        # Test creating a new association
        response = self.client.post(
            reverse('associate_card'),
            json.dumps({'credit_card': '1234567890123456', 'phone': '+1234567890'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        
        # Verify the association was created
        card = CreditCard.objects.get(card_number='1234567890123456')
        phone = PhoneNumber.objects.get(phone_number='+1234567890')
        self.assertTrue(phone.credit_cards.filter(id=card.id).exists())
        
    def test_retrieve_cards_single_phone(self):
        # Create test data
        card = CreditCard.objects.create(card_number='1234567890123456')
        phone = PhoneNumber.objects.create(phone_number='+1234567890')
        phone.credit_cards.add(card)
        
        # Test retrieving cards with a single phone number
        response = self.client.post(
            reverse('retrieve_cards'),
            json.dumps({'phone_numbers': ['+1234567890']}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('card_numbers', data)
        self.assertIn('1234567890123456', data['card_numbers'])
        
    def test_retrieve_cards_multiple_phones(self):
        # Create test data
        card1 = CreditCard.objects.create(card_number='1234567890123456')
        card2 = CreditCard.objects.create(card_number='6543210987654321')
        
        phone1 = PhoneNumber.objects.create(phone_number='+1234567890')
        phone2 = PhoneNumber.objects.create(phone_number='+0987654321')
        
        # Card1 is associated with both phones
        phone1.credit_cards.add(card1)
        phone2.credit_cards.add(card1)
        
        # Card2 is associated with only phone1
        phone1.credit_cards.add(card2)
        
        # Test retrieving cards with multiple phone numbers
        response = self.client.post(
            reverse('retrieve_cards'),
            json.dumps({'phone_numbers': ['+1234567890', '+0987654321']}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('card_numbers', data)
        self.assertIn('1234567890123456', data['card_numbers'])
        self.assertNotIn('6543210987654321', data['card_numbers'])
        
    def test_retrieve_cards_not_found(self):
        # Test retrieving cards with non-existent phone number
        response = self.client.post(
            reverse('retrieve_cards'),
            json.dumps({'phone_numbers': ['+nonexistent']}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)