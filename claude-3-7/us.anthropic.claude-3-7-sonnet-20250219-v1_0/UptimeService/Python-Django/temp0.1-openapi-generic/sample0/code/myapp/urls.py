
from django.urls import path
from . import views

urlpatterns = [
    path('heartbeat', views.heartbeat, name='heartbeat'),
    path('services', views.services, name='services'),
]