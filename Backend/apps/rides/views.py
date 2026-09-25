"""
API Views for the Rides app.

WHAT THESE VIEWS DO:
--------------------
These views handle all ride request operations — creating rides, listing
available rides, viewing ride details, updating rides, and cancelling rides.

VIEWS IN THIS FILE:
  1. RideCreateView: POST /api/rides/ — create a new ride request (riders only)
  2. MyRidesView: GET /api/rides/my-rides/ — list rides created by the logged-in rider
  3. AvailableRidesView: GET /api/rides/available/ — list biddable rides (drivers only)
  4. NearbyRidesView: GET /api/rides/nearby/ — find rides near a driver's location
  5. RideDetailView: GET /api/rides/<id>/ — view full details of a ride
  6. RideUpdateView: PATCH /api/rides/<id>/update/ — update a ride (ride owner only)
  7. RideCancelView: POST /api/rides/<id>/cancel/ — cancel a ride (ride owner only)

PERMISSION RULES:
  - Creating rides: riders only (drivers bid on rides, they don't create them)
  - Listing own rides: riders see their rides, drivers see rides they bid on
  - Available rides: drivers only (they need to see rides they can bid on)
  - Nearby rides: drivers only (geospatial query for rides near their location)
  - Ride detail: any authenticated user
  - Update/Cancel: ride owner (rider who created it) only

GEOSPATIAL QUERIES:
  The NearbyRidesView uses PostGIS ST_DWithin to find rides within a specified
  radius of the driver's current location. This uses the spatial indexes we
  defined on the PointFields for fast, efficient queries.
"""

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsRider, IsDriver

from .models import RideRequest
from .serializers import (
    RideCreateSerializer,
    RideListSerializer,
    RideDetailSerializer,
    RideUpdateSerializer,
)


class RideCreateView(APIView):
    """
    API endpoint for creating a new ride request.

    URL: POST /api/rides/
    Authentication: Required (JWT Bearer token)
    Permission: Riders only (drivers cannot create ride requests)

    REQUEST BODY (JSON):
    {
        "pickup_latitude": 17.3850,
        "pickup_longitude": 78.4867,
        "pickup_address": "Hitech City Metro Station, Hyderabad",
        "dropoff_latitude": 17.4399,
        "dropoff_longitude": 78.3810,
        "dropoff_address": "Gachibowli Stadium, Hyderabad",
        "vehicle_type": "sedan",
        "number_of_passengers": 2,
        "scheduled_time": "2026-04-25T10:00:00+05:30",
        "notes": "I have a suitcase"
    }

    SUCCESS RESPONSE (201 Created):
    {
        "message": "Ride request created successfully.",
        "ride": {
            "id": 1,
            "rider_username": "john_doe",
            "pickup_address": "Hitech City Metro Station, Hyderabad",
            ...
        }
    }
    """

    # Only authenticated riders can create ride requests.
    # IsAuthenticated checks the JWT token is valid.
    # IsRider checks that the user's role is 'rider'.
    # Both must pass — if either fails, the request is denied.
    permission_classes = [IsAuthenticated, IsRider]

    def post(self, request):
        """
        Handle POST request to create a new ride request.

        FLOW:
        1. Validate the incoming JSON data via RideCreateSerializer
        2. Serializer converts lat/lng into PostGIS Point objects
        3. Serializer creates the RideRequest in the database
        4. Return the created ride details using RideDetailSerializer

        The rider is automatically set from the JWT token (request.user),
        NOT from the request body. This is a security measure — it prevents
        users from creating rides on behalf of other users.

        Args:
            request: HTTP request with ride details in the body.

        Returns:
            Response: 201 with ride details, or 400 with validation errors.
        """
        # context={'request': request} passes the request to the serializer
        # so it can access request.user to set the rider.
        serializer = RideCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        ride = serializer.save()

        # ---------------------------------------------------------------
        # Phase 6: Background Tasks
        # Schedule the ride to auto-expire in 15 minutes (900 seconds)
        # if no bids are accepted.
        # ---------------------------------------------------------------
        from apps.tasks.tasks import expire_ride
        expire_ride.apply_async(args=[ride.id], countdown=900)

        # Use RideDetailSerializer for the response to include all fields
        # (including computed properties like is_biddable).
        return Response(
            {
                'message': 'Ride request created successfully.',
                'ride': RideDetailSerializer(ride).data,
            },
            status=status.HTTP_201_CREATED
        )


class MyRidesView(APIView):
    """
    API endpoint for listing the logged-in rider's own ride requests.

    URL: GET /api/rides/my-rides/
    Authentication: Required
    Permission: Riders only

    Returns all rides created by the authenticated rider, newest first.
    Supports filtering by status via query parameter:
      GET /api/rides/my-rides/?status=requested
      GET /api/rides/my-rides/?status=bidding
      GET /api/rides/my-rides/?status=completed

    RESPONSE (200 OK):
    {
        "count": 5,
        "rides": [
            {
                "id": 1,
                "pickup_address": "...",
                "status": "requested",
                ...
            },
            ...
        ]
    }
    """

    permission_classes = [IsAuthenticated, IsRider]

    def get(self, request):
        """
        List all ride requests created by the logged-in rider.

        QUERY PARAMETERS:
        - status (optional): filter by ride status
          Example: ?status=requested or ?status=bidding

        The queryset starts with all rides by this rider, then optionally
        filters by status if the query parameter is provided.

        select_related('rider') is an optimization: it tells Django to
        JOIN the users table in a single SQL query instead of making a
        separate query for each ride's rider. This is important because
        the serializer accesses obj.rider.username — without select_related,
        each ride would trigger an additional database query (N+1 problem).

        Args:
            request: HTTP request. request.user is the authenticated rider.

        Returns:
            Response: 200 with list of rides.
        """
        # Start with all rides created by this user.
        rides = RideRequest.objects.filter(
            rider=request.user
        ).select_related('rider')

        # Optional status filter from query parameters.
        # request.query_params is a dictionary-like object of URL parameters.
        status_filter = request.query_params.get('status')
        if status_filter:
            rides = rides.filter(status=status_filter)

        serializer = RideListSerializer(rides, many=True)

        return Response(
            {
                'count': rides.count(),
                'rides': serializer.data,
            },
            status=status.HTTP_200_OK
        )


class AvailableRidesView(APIView):
    """
    API endpoint for listing all rides available for bidding.

    URL: GET /api/rides/available/
    Authentication: Required
    Permission: Drivers only

    Returns rides with status 'requested' or 'bidding' — these are the
    rides that drivers can place bids on. Ordered by newest first.

    Supports filtering by vehicle type:
      GET /api/rides/available/?vehicle_type=sedan

    RESPONSE (200 OK):
    {
        "count": 12,
        "rides": [...]
    }
    """

    permission_classes = [IsAuthenticated, IsDriver]

    def get(self, request):
        """
        List all rides that are currently available for bidding.

        A ride is available for bidding if its status is either:
        - 'requested': just created, no bids yet
        - 'bidding': has bids but none accepted yet

        Drivers use this endpoint to browse available rides in the app
        and decide which ones to bid on.

        Args:
            request: HTTP request from a driver.

        Returns:
            Response: 200 with list of available rides.
        """
        rides = RideRequest.objects.filter(
            status__in=[RideRequest.Status.REQUESTED, RideRequest.Status.BIDDING]
        ).select_related('rider')

        # Optional vehicle type filter.
        vehicle_type = request.query_params.get('vehicle_type')
        if vehicle_type:
            # Filter rides that match the vehicle type OR accept 'any' vehicle.
            rides = rides.filter(
                vehicle_type__in=[vehicle_type, RideRequest.VehicleType.ANY]
            )

        serializer = RideListSerializer(rides, many=True)

        return Response(
            {
                'count': rides.count(),
                'rides': serializer.data,
            },
            status=status.HTTP_200_OK
        )


class NearbyRidesView(APIView):
    """
    API endpoint for finding rides near a driver's current location.

    URL: GET /api/rides/nearby/?lat=17.385&lng=78.487&radius=5
    Authentication: Required
    Permission: Drivers only

    This is the KEY geospatial endpoint that uses PostGIS for spatial queries.
    It finds all biddable rides whose PICKUP location is within a specified
    radius of the driver's current position.

    QUERY PARAMETERS (all required):
    - lat: driver's current latitude (float, -90 to 90)
    - lng: driver's current longitude (float, -180 to 180)
    - radius: search radius in KILOMETERS (float, default 5, max 50)

    HOW IT WORKS (under the hood):
    1. The driver's lat/lng is converted to a PostGIS Point
    2. PostGIS runs ST_DWithin(pickup_location, driver_point, radius)
    3. ST_DWithin uses the GiST spatial index for fast searching
    4. Only rides within the radius are returned, ordered by distance

    PERFORMANCE:
    Without PostGIS, we'd have to load ALL rides from the database and
    calculate the Haversine distance in Python for each one — O(n) with
    high constant factor. With PostGIS + GiST index, the query is O(log n)
    and runs entirely in the database.

    RESPONSE (200 OK):
    {
        "count": 3,
        "radius_km": 5.0,
        "rides": [...]
    }
    """

    permission_classes = [IsAuthenticated, IsDriver]

    def get(self, request):
        """
        Find rides near the driver's current location.

        STEP-BY-STEP:
        1. Extract and validate lat, lng, radius from query params
        2. Create a PostGIS Point from the driver's coordinates
        3. Query rides with pickup_location within radius km
        4. Return matching rides, ordered by distance (nearest first)

        Args:
            request: HTTP request with lat, lng, radius query params.

        Returns:
            Response: 200 with nearby rides, or 400 if params are invalid.
        """
        # ---------------------------------------------------------------
        # Extract query parameters.
        # request.query_params.get() returns None if the param is missing.
        # ---------------------------------------------------------------
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = request.query_params.get('radius', '5')  # default 5 km

        # Validate that required parameters are present.
        if not lat or not lng:
            return Response(
                {'error': 'Both "lat" and "lng" query parameters are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            lat = float(lat)
            lng = float(lng)
            radius = float(radius)
        except (ValueError, TypeError):
            return Response(
                {'error': '"lat", "lng", and "radius" must be valid numbers.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate coordinate ranges.
        if not -90 <= lat <= 90:
            return Response(
                {'error': 'Latitude must be between -90 and 90.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not -180 <= lng <= 180:
            return Response(
                {'error': 'Longitude must be between -180 and 180.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if radius <= 0 or radius > 50:
            return Response(
                {'error': 'Radius must be between 0 and 50 km.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ---------------------------------------------------------------
        # Create a PostGIS Point from the driver's coordinates.
        # Point(x, y) = Point(longitude, latitude) — lng comes first!
        # ---------------------------------------------------------------
        driver_location = Point(lng, lat, srid=4326)

        # ---------------------------------------------------------------
        # Query: find rides within the radius.
        #
        # pickup_location__dwithin: PostGIS ST_DWithin function.
        # D(km=radius): distance object — "within X kilometers".
        # The D class converts km to the appropriate unit for the
        # geographic coordinate system (meters internally).
        #
        # This query uses the GiST spatial index on pickup_location
        # for fast spatial filtering.
        # ---------------------------------------------------------------
        rides = RideRequest.objects.filter(
            status__in=[RideRequest.Status.REQUESTED, RideRequest.Status.BIDDING],
            pickup_location__dwithin=(driver_location, D(km=radius)),
        ).select_related('rider')

        serializer = RideListSerializer(rides, many=True)

        return Response(
            {
                'count': rides.count(),
                'radius_km': radius,
                'rides': serializer.data,
            },
            status=status.HTTP_200_OK
        )


class RideDetailView(APIView):
    """
    API endpoint for viewing full details of a specific ride.

    URL: GET /api/rides/<id>/
    Authentication: Required
    Permission: Any authenticated user

    Any authenticated user (rider or driver) can view ride details.
    This is needed because:
    - Riders need to see their own ride details
    - Drivers need to see ride details before deciding to bid

    RESPONSE (200 OK):
    {
        "id": 1,
        "rider_username": "john_doe",
        "pickup_address": "Hitech City Metro Station",
        "pickup_coords": {"latitude": 17.385, "longitude": 78.487},
        "is_biddable": true,
        "is_active": true,
        ...
    }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, ride_id):
        """
        Return full details of a specific ride request.

        Args:
            request: HTTP request from an authenticated user.
            ride_id (int): The primary key of the ride to retrieve.

        Returns:
            Response: 200 with ride details, or 404 if ride not found.
        """
        try:
            ride = RideRequest.objects.select_related('rider').get(pk=ride_id)
        except RideRequest.DoesNotExist:
            return Response(
                {'error': 'Ride request not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = RideDetailSerializer(ride)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RideUpdateView(APIView):
    """
    API endpoint for updating a ride request.

    URL: PATCH /api/rides/<id>/update/
    Authentication: Required
    Permission: Ride owner (rider who created it) only

    Only the rider who created the ride can update it, and only while
    the ride is still in 'requested' or 'bidding' status.

    UPDATABLE FIELDS:
    - vehicle_type
    - number_of_passengers
    - scheduled_time
    - notes

    REQUEST BODY (JSON, partial):
    {
        "vehicle_type": "suv",
        "notes": "Changed my mind, I have luggage now"
    }
    """

    permission_classes = [IsAuthenticated, IsRider]

    def patch(self, request, ride_id):
        """
        Partially update a ride request.

        FLOW:
        1. Find the ride by ID
        2. Verify the requesting user is the ride owner
        3. Validate and apply the updates
        4. Return updated ride details

        Args:
            request: HTTP request with fields to update.
            ride_id (int): The primary key of the ride to update.

        Returns:
            Response: 200 with updated ride, 403 if not owner, 404 if not found.
        """
        try:
            ride = RideRequest.objects.select_related('rider').get(pk=ride_id)
        except RideRequest.DoesNotExist:
            return Response(
                {'error': 'Ride request not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Security check: only the rider who created this ride can update it.
        if ride.rider != request.user:
            return Response(
                {'error': 'You can only update your own ride requests.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # partial=True allows updating only the fields that are provided,
        # leaving the rest unchanged (PATCH semantics).
        serializer = RideUpdateSerializer(
            instance=ride,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Return the full ride detail using the detail serializer.
        return Response(
            {
                'message': 'Ride request updated successfully.',
                'ride': RideDetailSerializer(ride).data,
            },
            status=status.HTTP_200_OK
        )


class RideCancelView(APIView):
    """
    API endpoint for cancelling a ride request.

    URL: POST /api/rides/<id>/cancel/
    Authentication: Required
    Permission: Ride owner (rider who created it) only

    Cancels a ride request. Only possible when the ride is in:
    - 'requested': no bids yet
    - 'bidding': bids exist but none accepted
    - 'accepted': bid accepted but trip hasn't started

    Cannot cancel once the ride is 'in_progress', 'completed', or
    already 'cancelled'.

    SUCCESS RESPONSE (200 OK):
    {
        "message": "Ride request cancelled successfully.",
        "ride": { ... }
    }
    """

    permission_classes = [IsAuthenticated, IsRider]

    def post(self, request, ride_id):
        """
        Cancel a ride request.

        FLOW:
        1. Find the ride by ID
        2. Verify the requesting user is the ride owner
        3. Check if the ride can still be cancelled
        4. Set status to 'cancelled' and save
        5. Return the updated ride

        Args:
            request: HTTP request from the ride owner.
            ride_id (int): The primary key of the ride to cancel.

        Returns:
            Response: 200 on success, 400 if can't cancel, 403 if not owner.
        """
        try:
            ride = RideRequest.objects.select_related('rider').get(pk=ride_id)
        except RideRequest.DoesNotExist:
            return Response(
                {'error': 'Ride request not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Security check: only the ride owner can cancel.
        if ride.rider != request.user:
            return Response(
                {'error': 'You can only cancel your own ride requests.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Business logic check: can this ride still be cancelled?
        if not ride.can_cancel:
            return Response(
                {
                    'error': f'Cannot cancel a ride with status "{ride.get_status_display()}". '
                             f'Only rides that are requested, bidding, or accepted can be cancelled.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update the status to cancelled.
        # update_fields=['status', 'updated_at'] is an optimization that tells
        # Django to only update these two columns, not all columns.
        ride.status = RideRequest.Status.CANCELLED
        ride.save(update_fields=['status', 'updated_at'])

        return Response(
            {
                'message': 'Ride request cancelled successfully.',
                'ride': RideDetailSerializer(ride).data,
            },
            status=status.HTTP_200_OK
        )
