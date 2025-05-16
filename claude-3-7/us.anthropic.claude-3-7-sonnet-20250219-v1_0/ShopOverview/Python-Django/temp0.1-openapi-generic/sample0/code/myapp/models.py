
from django.db import models

class Merchant(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=255)  # Will be hashed
    
    def __str__(self):
        return self.name

class Ware(models.Model):
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name='wares')
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.name