
from django.db import models
from django.contrib.auth.models import User

class Secret(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    secret_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Secret for {self.user.username}"