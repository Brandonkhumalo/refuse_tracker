import dramatiq
from dramatiq.brokers.redis import RedisBroker

redis_broker = RedisBroker(url='redis://default:lYggMnABfnrFgJrFFrEmWkKfhsBwrTyF@mainline.proxy.rlwy.net:36553')
dramatiq.set_broker(redis_broker)