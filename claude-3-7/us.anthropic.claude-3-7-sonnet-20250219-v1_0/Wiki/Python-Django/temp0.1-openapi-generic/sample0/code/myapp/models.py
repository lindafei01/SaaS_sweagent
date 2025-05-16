
from django.db import models
import uuid

class Entry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=255)
    last_modified_at = models.DateTimeField(auto_now=True)
    last_modified_by = models.CharField(max_length=255)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Entries"

class Edit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name='edits')
    content = models.TextField()
    modified_by = models.CharField(max_length=255)
    modified_at = models.DateTimeField(auto_now_add=True)
    summary = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"Edit on {self.entry.title} by {self.modified_by} at {self.modified_at}"