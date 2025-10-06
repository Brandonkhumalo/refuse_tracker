from django.urls import path, re_path
from .consumers import TruckTrackingConsumer
1
websocket_urlpatterns = [
    # Global trucks WebSocket (drivers/admins send updates here)
    re_path(r"ws/trucks/$", TruckTrackingConsumer.as_asgi()),

    # Residents connect to suburb-specific updates
    # Example: ws://127.0.0.1:8000/ws/trucks/resident/
    re_path(r"ws/trucks/resident/$", TruckTrackingConsumer.as_asgi()),
]
