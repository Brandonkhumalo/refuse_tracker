from django.apps import AppConfig
from dramatiq.brokers.redis import RedisBroker
from django.conf import settings
import dramatiq

class RefuseTrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'refuse_tracker'

    def ready(self):
        # Initialize Dramatiq broker
        redis_broker = RedisBroker(url=settings.REDIS_URL)
        dramatiq.set_broker(redis_broker)
