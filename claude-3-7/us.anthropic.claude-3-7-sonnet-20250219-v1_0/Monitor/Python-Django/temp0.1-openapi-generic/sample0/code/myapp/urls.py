
from django.urls import path
from . import views

urlpatterns = [
    path('monitor/commands', views.monitor_commands, name='monitor_commands'),
]