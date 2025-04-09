"""
ASGI config for chatbot_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""
# chatbot_project/asgi.py
import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import chatbot.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot_project.settings')
django.setup()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chatbot.routing.websocket_urlpatterns
        )
    ),
})

