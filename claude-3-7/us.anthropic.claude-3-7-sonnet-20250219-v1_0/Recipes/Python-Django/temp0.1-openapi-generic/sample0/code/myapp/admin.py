
from django.contrib import admin
from .models import Recipe, Comment, Rating

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'comment', 'created_at')
    list_filter = ('recipe',)

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'rating', 'created_at')
    list_filter = ('recipe', 'rating')