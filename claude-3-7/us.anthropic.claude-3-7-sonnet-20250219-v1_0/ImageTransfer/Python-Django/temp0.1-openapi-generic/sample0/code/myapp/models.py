
from django.db import models
import uuid
import os

def get_image_path(instance, filename):
    """Generate a unique path for uploaded images"""
    ext = filename.split('.')[-1]
    filename = f"{instance.id}.{ext}"
    return os.path.join('images', filename)

class Image(models.Model):
    """Model for storing uploaded images"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ImageField(upload_to=get_image_path)
    content_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return str(self.id)