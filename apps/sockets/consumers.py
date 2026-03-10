"""
WebSocket Consumers for the Sockets app.

WHAT IS A CONSUMER?
-------------------
In Django HTTP views, a request comes in, the view processes it, returns a response,
and the connection immediately closes.

In WebSockets, the connection stays open indefinitely. A Consumer is a class that
manages this long-lived connection. It listens for incoming messages from the client
and can push messages to the client at any time.

HOW WE USE CHANNELS & REDIS:
When a driver places a bid via a standard HTTP POST request (in the bids app),
that HTTP view cannot directly talk to the rider's WebSocket connection because
they are handled by different processes.

Instead, we use Redis as a "Channel Layer" (message broker):
1. Rider connects WebSocket → Consumer adds them to a Redis "Group" named 'ride_5'
2. Driver places bid via HTTP → View sends a message to the Redis Group 'ride_5'
3. Redis broadcasts the message to all Consumers in 'ride_5'
4. Consumer receives the message and pushes it down the WebSocket to the Rider.
"""

import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

from apps.rides.models import RideRequest


class RideConsumer(AsyncWebsocketConsumer):
    """
    Consumer that handles real-time updates for a specific ride.
    
    URL: ws://localhost:8000/ws/rides/<ride_id>/?token=<jwt>
    """

    async def connect(self):
        """
        Called when a client attempts to open a WebSocket connection.
        """
        # The user was attached to the scope by our JWTAuthMiddleware
        self.user = self.scope['user']

        # Reject unauthenticated users
        if isinstance(self.user, AnonymousUser):
            await self.close(code=4001)  # 4001 = Unauthorized
            return

        # Extract the ride_id from the URL route kwargs
        self.ride_id = self.scope['url_route']['kwargs']['ride_id']
        
        # Verify the ride exists and the user is allowed to listen to it.
        # Riders should only listen to their own rides.
        is_valid = await self.verify_ride_access()
        if not is_valid:
            await self.close(code=4003)  # 4003 = Forbidden
            return

        # Define the group name. It must be a valid string without special chars.
        # Example: "ride_5"
        self.ride_group_name = f'ride_{self.ride_id}'

        # Add this connection to the Redis group
        await self.channel_layer.group_add(
            self.ride_group_name,
            self.channel_name
        )

        # Accept the WebSocket connection
        await self.accept()

        # Send a welcome message confirming successful connection
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'Successfully connected to updates for ride {self.ride_id}.'
        }))

    async def disconnect(self, close_code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Remove this connection from the Redis group
        if hasattr(self, 'ride_group_name'):
            await self.channel_layer.group_discard(
                self.ride_group_name,
                self.channel_name
            )

    @database_sync_to_async
    def verify_ride_access(self):
        """
        Verify that the ride exists and the user has permission to subscribe to it.
        Wrapped in @database_sync_to_async because it queries the DB.
        """
        try:
            ride = RideRequest.objects.get(pk=self.ride_id)
            
            # For Phase 5, we only allow the Rider who created the ride to subscribe
            # to its updates. (Drivers don't need real-time updates on a ride until
            # they are assigned, at which point the logic might expand).
            if ride.rider_id == self.user.id:
                return True
            return False
            
        except RideRequest.DoesNotExist:
            return False

    # =================================================================
    # CUSTOM EVENT HANDLERS
    # =================================================================
    # These methods are triggered by the Channel Layer when another part
    # of the system (like an HTTP view) sends a message to the group.
    # The method name MUST match the 'type' in the message payload.
    # For example, a message with type='bid.placed' triggers bid_placed().
    # =================================================================

    async def bid_placed(self, event):
        """
        Called when a driver places a new bid.
        """
        # We just forward the event data directly to the WebSocket client
        await self.send(text_data=json.dumps({
            'type': 'BID_PLACED',
            'data': event['bid_data']
        }))

    async def bid_accepted(self, event):
        """
        Called when a bid is accepted.
        """
        await self.send(text_data=json.dumps({
            'type': 'BID_ACCEPTED',
            'data': event['bid_data']
        }))

    async def bid_cancelled(self, event):
        """
        Called when a driver cancels their bid.
        """
        await self.send(text_data=json.dumps({
            'type': 'BID_CANCELLED',
            'data': event['bid_data']
        }))
