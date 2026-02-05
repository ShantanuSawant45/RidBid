"""
URL routing for the Rides app.

HOW THESE URLS CONNECT TO THE REST OF THE PROJECT:
---------------------------------------------------
These URL patterns are mounted at 'api/rides/' by config/urls.py.
So the full URLs become:

  POST   /api/rides/                    → RideCreateView (create a ride)
  GET    /api/rides/my-rides/           → MyRidesView (rider's own rides)
  GET    /api/rides/available/          → AvailableRidesView (biddable rides)
  GET    /api/rides/nearby/             → NearbyRidesView (geospatial search)
  GET    /api/rides/<id>/               → RideDetailView (single ride detail)
  PATCH  /api/rides/<id>/update/        → RideUpdateView (edit a ride)
  POST   /api/rides/<id>/cancel/        → RideCancelView (cancel a ride)

URL DESIGN RATIONALE:
- List/Create are at the root (/api/rides/)
- Action endpoints use verbs (/cancel/, /update/) for clarity
- Detail views use the ride ID as a path parameter (<int:ride_id>/)
- <int:ride_id> tells Django to match only integer values and pass
  them to the view as a keyword argument named 'ride_id'
"""

from django.urls import path

from .views import (
    RideCreateView,
    MyRidesView,
    AvailableRidesView,
    NearbyRidesView,
    RideDetailView,
    RideUpdateView,
    RideCancelView,
)

# Namespace for URL reversing. Allows: reverse('rides:ride-create')
app_name = 'rides'

urlpatterns = [
    # ---------------------------------------------------------------
    # Create a new ride request.
    # Method: POST
    # Auth: Riders only
    # Body: {pickup_latitude, pickup_longitude, pickup_address, ...}
    # Returns: created ride details + tokens
    # ---------------------------------------------------------------
    path(
        '',
        RideCreateView.as_view(),
        name='ride-create'
    ),

    # ---------------------------------------------------------------
    # List the authenticated rider's own ride requests.
    # Method: GET
    # Auth: Riders only
    # Query Params: ?status=requested (optional filter)
    # Returns: list of rider's rides
    # ---------------------------------------------------------------
    path(
        'my-rides/',
        MyRidesView.as_view(),
        name='my-rides'
    ),

    # ---------------------------------------------------------------
    # List all rides available for bidding.
    # Method: GET
    # Auth: Drivers only
    # Query Params: ?vehicle_type=sedan (optional filter)
    # Returns: list of biddable rides
    # ---------------------------------------------------------------
    path(
        'available/',
        AvailableRidesView.as_view(),
        name='available-rides'
    ),

    # ---------------------------------------------------------------
    # Find rides near a driver's current location (geospatial query).
    # Method: GET
    # Auth: Drivers only
    # Query Params: ?lat=17.385&lng=78.487&radius=5 (required)
    # Returns: rides within radius km of the driver
    # ---------------------------------------------------------------
    path(
        'nearby/',
        NearbyRidesView.as_view(),
        name='nearby-rides'
    ),

    # ---------------------------------------------------------------
    # View full details of a specific ride.
    # Method: GET
    # Auth: Any authenticated user
    # URL Param: ride_id (integer)
    # Returns: full ride details including computed properties
    # ---------------------------------------------------------------
    path(
        '<int:ride_id>/',
        RideDetailView.as_view(),
        name='ride-detail'
    ),

    # ---------------------------------------------------------------
    # Update a ride request (partial update).
    # Method: PATCH
    # Auth: Ride owner (rider who created it)
    # URL Param: ride_id (integer)
    # Body: {vehicle_type, number_of_passengers, scheduled_time, notes}
    # ---------------------------------------------------------------
    path(
        '<int:ride_id>/update/',
        RideUpdateView.as_view(),
        name='ride-update'
    ),

    # ---------------------------------------------------------------
    # Cancel a ride request.
    # Method: POST
    # Auth: Ride owner (rider who created it)
    # URL Param: ride_id (integer)
    # Returns: cancelled ride details
    # ---------------------------------------------------------------
    path(
        '<int:ride_id>/cancel/',
        RideCancelView.as_view(),
        name='ride-cancel'
    ),
]
