import os
from channels.routing import ProtocolTypeRouter, URLRouter
from refuse_tracker.middleware import JWTAuthMiddleware
from django.core.asgi import get_asgi_application
import refuse_tracker.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zim_refuse_tracker.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
        URLRouter(
            refuse_tracker.routing.websocket_urlpatterns
        )
    ),
})
