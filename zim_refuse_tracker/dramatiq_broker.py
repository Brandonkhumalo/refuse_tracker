import dramatiq
from dramatiq.brokers.redis import RedisBroker
from .settings import REDIS_URL  # adjust path if needed

# Create the Redis broker
broker = RedisBroker(url=REDIS_URL)

# Register it as the default broker
dramatiq.set_broker(broker)
