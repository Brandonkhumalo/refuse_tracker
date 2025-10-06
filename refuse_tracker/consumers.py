import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

class TruckTrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user", None) or "anonymous"

        # Join the main truck group
        await self.channel_layer.group_add("trucks", self.channel_name)

        # Handle suburb-based subscriptions for residents
        if getattr(self.user, "role", None) == "resident" and getattr(self.user, "suburb", None):
            self.suburb_group = f"suburb_{self.user.suburb.lower()}"
            await self.channel_layer.group_add(self.suburb_group, self.channel_name)

        await self.accept()

        # If the frontend connects with ?truck_id=ID, send last DB location
        query_string = self.scope.get("query_string", b"").decode()
        if "truck_id" in query_string:
            try:
                import urllib.parse
                params = urllib.parse.parse_qs(query_string)
                truck_id = int(params.get("truck_id", [None])[0])
                last_location = await self.get_latest_location(truck_id)

                if last_location:
                    await self.send(text_data=json.dumps({
                        "type": "truck_update",
                        "truck_id": truck_id,
                        "latitude": last_location["latitude"],
                        "longitude": last_location["longitude"],
                        "timestamp": str(last_location["timestamp"]),
                        "from_db": True
                    }))
            except Exception as e:
                print(f"[ERROR sending last location] {e}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("trucks", self.channel_name)
        if hasattr(self, "suburb_group"):
            await self.channel_layer.group_discard(self.suburb_group, self.channel_name)

    async def receive(self, text_data):
        """Receive truck location and broadcast"""
        data = json.loads(text_data)
        truck_id = data["truck_id"]
        truck_lat = data["latitude"]
        truck_lng = data["longitude"]

        from refuse_tracker.models import Truck, LocationUpdate
        from refuse_tracker.tasks import send_truck_proximity_alert

        # Save to DB
        location = await self.save_location(truck_id, truck_lat, truck_lng)

        # Broadcast globally
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

        # Broadcast to suburb
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

        # Dramatiq task
        send_truck_proximity_alert.send(truck_id, truck_lat, truck_lng)

    async def truck_update(self, event):
        """Send truck updates to frontend"""
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def save_location(self, truck_id, lat, lng):
        """Save the truck's latest location to the database"""
        from refuse_tracker.models import Truck, LocationUpdate
        truck = Truck.objects.get(pk=truck_id)
        return LocationUpdate.objects.create(
            truck=truck,
            latitude=lat,
            longitude=lng,
            timestamp=timezone.now()
        )

    @database_sync_to_async
    def get_latest_location(self, truck_id):
        """Fetch the last known location from DB"""
        from refuse_tracker.models import LocationUpdate
        last = LocationUpdate.objects.filter(truck_id=truck_id).order_by("-timestamp").first()
        if last:
            return {
                "latitude": last.latitude,
                "longitude": last.longitude,
                "timestamp": last.timestamp,
            }
        return None
