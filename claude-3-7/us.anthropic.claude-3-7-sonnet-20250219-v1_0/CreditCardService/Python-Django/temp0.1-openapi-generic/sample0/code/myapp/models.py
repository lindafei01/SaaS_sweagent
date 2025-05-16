
from django.db import models

class CreditCard(models.Model):
    card_number = models.CharField(max_length=255, unique=True)
    
    def __str__(self):
        return self.card_number

class PhoneNumber(models.Model):
    phone_number = models.CharField(max_length=255)
    credit_cards = models.ManyToManyField(CreditCard, related_name='phone_numbers')
    
    def __str__(self):
        return self.phone_number