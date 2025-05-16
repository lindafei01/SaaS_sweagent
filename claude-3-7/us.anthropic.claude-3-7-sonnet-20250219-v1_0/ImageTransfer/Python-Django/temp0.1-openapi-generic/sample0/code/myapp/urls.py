
from django.urls import path
from . import views

urlpatterns = [
    path('upload', views.upload_image, name='upload_image'),
    path('images/<str:imageId>', views.get_image, name='get_image'),
]