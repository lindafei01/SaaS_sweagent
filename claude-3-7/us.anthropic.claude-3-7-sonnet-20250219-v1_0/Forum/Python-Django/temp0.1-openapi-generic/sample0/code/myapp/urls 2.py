
from django.urls import path
from . import views

urlpatterns = [
    path('messages', views.messages_view, name='messages'),
    path('', views.index_view, name='index'),
]