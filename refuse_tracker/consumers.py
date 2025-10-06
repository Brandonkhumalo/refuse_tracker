import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

class TruckTrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Only trucks should connect here, authenticate if needed
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        truck_id = data["truck_id"]
        lat = data["latitude"]
        lng = data["longitude"]

        # Import models and tasks inside function to avoid AppRegistryNotReady
        from refuse_tracker.models import Truck, LocationUpdate
        from refuse_tracker.tasks import send_truck_proximity_alert

        location = await self.save_location(truck_id, lat, lng)

        # Broadcast to global "trucks" group
        await self.channel_layer.group_send(
            "trucks",
            {
                "type": "truck_update",
                "truck_id": truck_id,
                "latitude": lat,
                "longitude": lng,
                "timestamp": str(location.timestamp),
                "truck_name": f"Truck {truck_id}"
            }
        )

        # Trigger proximity alerts
        send_truck_proximity_alert.send(truck_id, lat, lng)

    @database_sync_to_async
    def save_location(self, truck_id, lat, lng):
        # Import models here as well
        from refuse_tracker.models import Truck, LocationUpdate
        truck = Truck.objects.get(pk=truck_id)
        return LocationUpdate.objects.create(
            truck=truck,
            latitude=lat,
            longitude=lng,
            timestamp=timezone.now()
        )

class ResidentTrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user", None) or "anonymous"

        # Join main trucks group
        await self.channel_layer.group_add("trucks", self.channel_name)

        # Optionally join suburb-specific group if resident has a suburb
        if getattr(self.user, "role", None) == "resident" and getattr(self.user, "suburb", None):
            self.suburb_group = f"suburb_{self.user.suburb.lower()}"
            await self.channel_layer.group_add(self.suburb_group, self.channel_name)

        await self.accept()

        # Optionally send last known truck location from DB
        await self.send_last_truck_location()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("trucks", self.channel_name)
        if hasattr(self, "suburb_group"):
            await self.channel_layer.group_discard(self.suburb_group, self.channel_name)

    async def truck_update(self, event):
        # Residents receive truck updates here
        await self.send(text_data=json.dumps(event))

    async def send_last_truck_location(self):
        # Delayed import
        from refuse_tracker.models import LocationUpdate

        # Example: get last known truck update
        last_location = await self.get_latest_location()
        if last_location:
            await self.send(text_data=json.dumps({
                "type": "truck_update",
                "truck_id": last_location["truck_id"],
                "latitude": last_location["latitude"],
                "longitude": last_location["longitude"],
                "timestamp": str(last_location["timestamp"]),
                "truck_name": last_location.get("truck_name", "Truck")
            }))

    @database_sync_to_async
    def get_latest_location(self):
        from refuse_tracker.models import LocationUpdate
        last = LocationUpdate.objects.order_by("-timestamp").first()
        if last:
            return {
                "truck_id": last.truck.id,
                "latitude": last.latitude,
                "longitude": last.longitude,
                "timestamp": last.timestamp,
                "truck_name": getattr(last.truck, "name", "Truck")
            }
        return None
