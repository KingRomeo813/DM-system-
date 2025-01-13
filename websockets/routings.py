from django.urls import path
from .sockets import SocketConsumer

websocket_urlpatterns = [

    path('ws/socket/', SocketConsumer.as_asgi()),

]