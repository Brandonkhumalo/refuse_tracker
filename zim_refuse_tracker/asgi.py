import os

# Must be set first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zim_refuse_tracker.settings')

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
import refuse_tracker.routing
from refuse_tracker.middleware import JWTAuthMiddleware

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
        URLRouter(
            refuse_tracker.routing.websocket_urlpatterns
        )
    ),
})
