
from django.db import models

class UserProfile(models.Model):
    username = models.CharField(max_length=100, unique=True)
    profile_page = models.TextField()  # Store HTML content
    profile_photo = models.BinaryField()  # Store PNG image as binary data
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.username