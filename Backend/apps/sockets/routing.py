"""
WebSocket Routing Configuration.

Similar to urls.py in Django, routing.py maps WebSocket URLs to Consumers.
"""

from django.urls import path

from .consumers import RideConsumer

websocket_urlpatterns = [
    # Using path() instead of re_path() for clean URL mapping.
    # Connects ws://domain/ws/rides/5/ to the RideConsumer.
    path('ws/rides/<int:ride_id>/', RideConsumer.as_asgi()),
]
