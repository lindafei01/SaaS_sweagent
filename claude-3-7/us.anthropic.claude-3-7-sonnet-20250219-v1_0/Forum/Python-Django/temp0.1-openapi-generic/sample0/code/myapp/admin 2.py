
from django.contrib import admin
from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('username', 'content', 'created_at')
    search_fields = ('username', 'content')
    list_filter = ('created_at',)