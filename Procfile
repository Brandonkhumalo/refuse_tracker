web: DJANGO_SETTINGS_MODULE=zim_refuse_tracker.settings daphne -b 0.0.0.0 -p 8000 zim_refuse_tracker.asgi:application
worker: DJANGO_SETTINGS_MODULE=zim_refuse_tracker.settings dramatiq refuse_tracker.tasks --processes 1 --threads 2
