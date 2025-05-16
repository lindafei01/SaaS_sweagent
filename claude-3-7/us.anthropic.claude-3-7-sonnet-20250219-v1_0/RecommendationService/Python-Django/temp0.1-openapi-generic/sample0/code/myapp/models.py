
from django.db import models

class Product(models.Model):
    """Model representing a product with associated tags."""
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Tag(models.Model):
    """Model representing a tag that can be associated with products."""
    name = models.CharField(max_length=100, unique=True)
    products = models.ManyToManyField(Product, related_name='tags')
    
    def __str__(self):
        return self.name