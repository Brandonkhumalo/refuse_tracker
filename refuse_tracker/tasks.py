import dramatiq
import os
import django
from geopy.distance import geodesic
from django.core.mail import send_mail

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zim_refuse_tracker.settings")
django.setup()

from .models import Truck, User

@dramatiq.actor
def send_truck_proximity_alert(truck_id, truck_lat, truck_lng):
    """
    Send email to residents if a truck is within 1 km of their house.
    """
    try:
        truck = Truck.objects.get(pk=truck_id)
    except Truck.DoesNotExist:
        return

    # Filter residents by truck's route/suburb
    residents = User.objects.filter(role='resident', suburb__icontains=truck.route_info)
    for resident in residents:
        if resident.lat and resident.lng:
            truck_pos = (truck_lat, truck_lng)
            resident_pos = (resident.lat, resident.lng)
            distance_km = geodesic(truck_pos, resident_pos).km
            if distance_km <= 1:
                send_mail(
                    subject=f"Refuse Truck Approaching ({truck.name})",
                    message=f"Hello {resident.email},\n\n"
                            f"The refuse truck ({truck.name}) is less than 1 km away from your house at {resident.suburb}.\n"
                            f"Please be ready for collection.\n\n"
                            f"Thank you,\nZimRefuse Team",
                    from_email=None,  # Will use DEFAULT_FROM_EMAIL from settings
                    recipient_list=[resident.email],
                    fail_silently=False  # Set to False so you get errors if email fails
                )
#dramatiq refuse_tracker.tasks --processes 1 --threads 2
#daphne -b 0.0.0.0 -p 8000 zim_refuse_tracker.asgi:application