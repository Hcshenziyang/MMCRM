# urls.py
from django.urls import path
from .views import ai_chat

urlpatterns = [
    path("ai/chat/", ai_chat),
]