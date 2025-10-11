from django.urls import path
from . import views
from . import authviews

urlpatterns = [
    # Users
    path('register/', authviews.create_user),
    path('login/', authviews.login_user),

    # Admin Trucks & Locations
    path('trucks/', views.trucks_list_create),
    path('trucks/<int:pk>/', views.truck_detail),
    path('locations/', views.locations_list_create),
    path('locations/<int:pk>/', views.location_detail),

    # Admin Schedules
    path('schedules/', views.schedules_list_create),
    path('schedules/<int:pk>/', views.schedule_detail),

    # Resident filtered views
    path('resident/schedules/', views.resident_schedules),
    path('resident/trucks/', views.resident_trucks),
    path('resident/locations/', views.resident_locations),

    path('profile/', views.user_profile, name='user_profile'),
    path('profile/update-suburb/', views.update_suburb, name='update_suburb'),
]
