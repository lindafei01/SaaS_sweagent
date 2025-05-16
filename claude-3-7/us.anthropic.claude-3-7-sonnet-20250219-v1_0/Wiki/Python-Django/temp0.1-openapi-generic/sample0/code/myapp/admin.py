
from django.contrib import admin
from .models import Entry, Edit

@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at', 'last_modified_by', 'last_modified_at')
    search_fields = ('title', 'content')
    readonly_fields = ('id', 'created_at', 'last_modified_at')

@admin.register(Edit)
class EditAdmin(admin.ModelAdmin):
    list_display = ('entry', 'modified_by', 'modified_at', 'summary')
    search_fields = ('entry__title', 'modified_by', 'summary')
    readonly_fields = ('id', 'modified_at')