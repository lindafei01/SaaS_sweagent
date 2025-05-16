
from django.urls import path
from . import views

urlpatterns = [
    path('log', views.log_message, name='log_message'),
    path('logs', views.get_logs, name='get_logs'),
]