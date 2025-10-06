import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from refuse_tracker.models import Truck, LocationUpdate
from refuse_tracker.tasks import send_truck_proximity_alert

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

        send_truck_proximity_alert.send(truck_id, lat, lng)

    @database_sync_to_async
    def save_location(self, truck_id, lat, lng):
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

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("trucks", self.channel_name)
        if hasattr(self, "suburb_group"):
            await self.channel_layer.group_discard(self.suburb_group, self.channel_name)

    async def truck_update(self, event):
        # Residents receive truck updates here
        await self.send(text_data=json.dumps(event))