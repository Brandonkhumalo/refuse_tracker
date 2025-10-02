import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

class TruckTrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Only allow authenticated users
        if self.scope["user"].is_anonymous:
            await self.close()
            return

        self.user = self.scope["user"]

        # Join global trucks group
        await self.channel_layer.group_add("trucks", self.channel_name)

        # If resident, join their suburb-specific group
        if getattr(self.user, "role", None) == "resident" and getattr(self.user, "suburb", None):
            self.suburb_group = f"suburb_{self.user.suburb.lower()}"
            await self.channel_layer.group_add(self.suburb_group, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("trucks", self.channel_name)
        if hasattr(self, "suburb_group"):
            await self.channel_layer.group_discard(self.suburb_group, self.channel_name)

    async def receive(self, text_data):
        """
        Receive truck location from WebSocket, save to DB, broadcast to group, 
        and trigger async proximity check.
        Expected message format:
        {
            "truck_id": 1,
            "latitude": -17.823,
            "longitude": 31.043
        }
        """
        data = json.loads(text_data)
        truck_id = data["truck_id"]
        truck_lat = data["latitude"]
        truck_lng = data["longitude"]

        # Lazy import models to avoid AppRegistryNotReady
        from refuse_tracker.models import Truck, LocationUpdate
        from refuse_tracker.tasks import send_truck_proximity_alert

        # Save location update in DB
        location = await self.save_location(truck_id, truck_lat, truck_lng)

        # Broadcast to global group (admins/monitors)
        await self.channel_layer.group_send(
            "trucks",
            {
                "type": "truck_update",
                "truck_id": truck_id,
                "latitude": truck_lat,
                "longitude": truck_lng,
                "timestamp": str(location.timestamp),
            }
        )

        # Broadcast to suburb-specific group
        truck = await database_sync_to_async(Truck.objects.get)(pk=truck_id)
        suburb_group = f"suburb_{truck.route_info.lower()}"
        await self.channel_layer.group_send(
            suburb_group,
            {
                "type": "truck_update",
                "truck_id": truck_id,
                "latitude": truck_lat,
                "longitude": truck_lng,
                "timestamp": str(location.timestamp),
            }
        )

        # Enqueue Dramatiq task to send proximity alerts asynchronously
        send_truck_proximity_alert.send(truck_id, truck_lat, truck_lng)

    async def truck_update(self, event):
        """
        Deliver updates to connected clients.
        Residents will only get updates if in their suburb group.
        """
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def save_location(self, truck_id, lat, lng):
        """Save the latest location update to the database"""
        # Lazy import models to avoid AppRegistryNotReady
        from refuse_tracker.models import Truck, LocationUpdate

        truck = Truck.objects.get(pk=truck_id)
        return LocationUpdate.objects.create(
            truck=truck,
            latitude=lat,
            longitude=lng,
            timestamp=timezone.now()
        )
