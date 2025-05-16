
from django.contrib import admin
from .models import Invitation

@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'invite_id', 'created_at', 'created_by', 'is_used')
    search_fields = ('email', 'invite_id')
    list_filter = ('is_used', 'created_at')