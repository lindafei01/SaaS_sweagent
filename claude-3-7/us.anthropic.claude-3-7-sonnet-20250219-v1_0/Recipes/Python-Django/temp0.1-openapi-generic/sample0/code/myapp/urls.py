
from django.urls import path
from . import views

urlpatterns = [
    path('recipes', views.recipes_overview, name='recipes_overview'),
    path('recipes/upload', views.upload_recipe, name='upload_recipe'),
    path('recipes/<str:recipe_id>', views.get_recipe, name='get_recipe'),
    path('recipes/<str:recipe_id>/comments', views.add_comment, name='add_comment'),
    path('recipes/<str:recipe_id>/ratings', views.add_rating, name='add_rating'),
]