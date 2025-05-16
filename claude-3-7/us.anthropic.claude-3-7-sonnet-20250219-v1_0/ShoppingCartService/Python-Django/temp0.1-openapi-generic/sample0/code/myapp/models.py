
from django.db import models
import uuid

class Cart(models.Model):
    """Model representing a shopping cart."""
    cart_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.cart_id)

class CartItem(models.Model):
    """Model representing an item in a shopping cart."""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    item_id = models.IntegerField()
    count = models.IntegerField(default=0)
    
    class Meta:
        # Ensure that each item_id appears only once per cart
        unique_together = ('cart', 'item_id')
    
    def __str__(self):
        return f"Cart: {self.cart.cart_id}, Item: {self.item_id}, Count: {self.count}"