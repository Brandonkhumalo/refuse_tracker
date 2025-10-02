web: daphne -b 0.0.0.0 -p 8000 refuse_tracker.asgi:application
worker: dramatiq refuse_tracker.tasks --processes 1 --threads 2
