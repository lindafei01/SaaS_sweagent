
from django.urls import path
from . import views

urlpatterns = [
    path('convert', views.convert_zip_to_text, name='convert_zip_to_text'),
]