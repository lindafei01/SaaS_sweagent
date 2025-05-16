
from django.db import models
from django.contrib.auth.models import User
import uuid

class Invitation(models.Model):
    invite_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Invitation for {self.email} ({self.invite_id})"