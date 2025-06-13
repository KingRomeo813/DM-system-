import os, django
django.setup()
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from websockets import routings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routings.websocket_urlpatterns
        )
    ),
})