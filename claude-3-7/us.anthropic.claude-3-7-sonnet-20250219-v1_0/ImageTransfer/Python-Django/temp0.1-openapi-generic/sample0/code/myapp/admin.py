
from django.contrib import admin
from .models import Image

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'content_type', 'uploaded_at')
    readonly_fields = ('id', 'uploaded_at')