from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid

class User(AbstractUser):
    ROLE_CHOICES = (
        ('resident', 'Resident'),
        ('admin', 'Admin'),
    )

    # Remove username field
    username = None  

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    suburb = models.CharField(max_length=100, blank=True, null=True)

    # Override groups and user_permissions to avoid reverse accessor clashes
    groups = models.ManyToManyField(Group, verbose_name=_('groups'), blank=True,related_name="refuse_tracker_users")
    user_permissions = models.ManyToManyField(Permission, verbose_name=_('user permissions'),
        blank=True, related_name="refuse_tracker_user_permissions")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

class Truck(models.Model):
    name = models.CharField(max_length=100)
    gps_device_id = models.CharField(max_length=100, unique=True)
    route_info = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Schedule(models.Model):
    truck = models.ForeignKey(Truck, on_delete=models.CASCADE, related_name="schedules")  # link schedule to truck
    suburb = models.CharField(max_length=100)
    route = models.CharField(max_length=100)
    collection_date = models.DateField()

    def __str__(self):
        return f"{self.truck.name} - {self.suburb} ({self.collection_date})"

class LocationUpdate(models.Model):
    truck = models.ForeignKey(Truck, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.truck.name} @ {self.timestamp}"

class BlacklistedToken(models.Model):
    token = models.CharField(max_length=255, unique=True)
    blacklisted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Blacklisted at {self.blacklisted_at}"