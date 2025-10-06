import dramatiq
from dramatiq.brokers.redis import RedisBroker
from .settings import REDIS_URL  # adjust path if needed

if not REDIS_URL:
    raise ValueError("REDIS_URL environment variable is not set!")

broker = RedisBroker(url=REDIS_URL)
dramatiq.set_broker(broker)
