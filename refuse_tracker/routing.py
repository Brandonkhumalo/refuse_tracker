from django.urls import path, re_path
from .consumers import TruckTrackingConsumer, ResidentTrackingConsumer
1
websocket_urlpatterns = [
    # Global trucks WebSocket (drivers/admins send updates here)
    re_path(r"ws/trucks/$", TruckTrackingConsumer.as_asgi()),

    # Residents connect to suburb-specific updates3
    re_path(r"ws/trucks/resident/$", ResidentTrackingConsumer.as_asgi()),
]
