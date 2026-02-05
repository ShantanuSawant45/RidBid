"""
Serializers for the Rides app.

WHAT THESE SERIALIZERS DO:
--------------------------
These serializers handle the conversion between JSON (sent by the mobile app)
and Python/Django model instances (stored in the database) for ride requests.

SERIALIZERS IN THIS FILE:
  1. RideCreateSerializer: handles creating a new ride request
     - Accepts pickup/dropoff coordinates + addresses + preferences
     - Validates coordinates are real geographic points
     - Automatically sets the rider from the JWT token

  2. RideListSerializer: handles listing rides (compact view)
     - Returns a summarized view of rides for list endpoints
     - Includes rider username, addresses, status, vehicle type

  3. RideDetailSerializer: handles viewing a single ride (full view)
     - Returns all ride details including coordinates
     - Includes computed fields like is_biddable and is_active

  4. RideUpdateSerializer: handles updating a ride request
     - Only allows updating certain fields (notes, scheduled_time, etc.)
     - Prevents changing critical fields like locations after creation

COORDINATE HANDLING:
The mobile app sends coordinates as simple numbers:
  {"pickup_latitude": 17.385, "pickup_longitude": 78.4867, ...}

We convert these into PostGIS Point objects:
  Point(78.4867, 17.385, srid=4326)

This conversion happens in the create() method because PostGIS Point
objects can't be directly deserialized from JSON — they need special handling.
"""

from django.contrib.gis.geos import Point

from rest_framework import serializers

from .models import RideRequest


class RideCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new ride request.

    WHAT THE CLIENT SENDS (JSON):
    {
        "pickup_latitude": 17.3850,
        "pickup_longitude": 78.4867,
        "pickup_address": "Hitech City Metro Station, Hyderabad",
        "dropoff_latitude": 17.4399,
        "dropoff_longitude": 78.3810,
        "dropoff_address": "Gachibowli Stadium, Hyderabad",
        "vehicle_type": "sedan",       // optional, defaults to "any"
        "number_of_passengers": 2,     // optional, defaults to 1
        "scheduled_time": "2026-04-25T10:00:00+05:30",  // optional (null = ASAP)
        "notes": "I have a suitcase"   // optional
    }

    WHY SEPARATE LAT/LNG FIELDS?
    The client sends latitude and longitude as separate float numbers because
    that's how GPS coordinates work naturally. But PostGIS stores them as a
    single Point object. So we accept them as separate fields and combine
    them into a Point in the create() method.

    We DON'T expose the raw PointField (pickup_location, dropoff_location)
    because DRF doesn't know how to serialize/deserialize PostGIS geometry
    objects from plain JSON without extra libraries.
    """

    # ---------------------------------------------------------------
    # Custom input fields for coordinates.
    # These are NOT model fields — they exist only for this serializer.
    # write_only=True: accepted in input but never returned in responses.
    #
    # Latitude: north-south position, ranges from -90 to +90
    #   - Positive = North (e.g., 17.385 is Hyderabad)
    #   - Negative = South (e.g., -33.87 is Sydney)
    #
    # Longitude: east-west position, ranges from -180 to +180
    #   - Positive = East (e.g., 78.49 is Hyderabad)
    #   - Negative = West (e.g., -73.99 is New York)
    # ---------------------------------------------------------------
    pickup_latitude = serializers.FloatField(
        write_only=True,
        help_text="Pickup latitude (-90 to 90). Example: 17.3850"
    )
    pickup_longitude = serializers.FloatField(
        write_only=True,
        help_text="Pickup longitude (-180 to 180). Example: 78.4867"
    )
    dropoff_latitude = serializers.FloatField(
        write_only=True,
        help_text="Dropoff latitude (-90 to 90). Example: 17.4399"
    )
    dropoff_longitude = serializers.FloatField(
        write_only=True,
        help_text="Dropoff longitude (-180 to 180). Example: 78.3810"
    )

    class Meta:
        model = RideRequest
        fields = [
            'id',
            'pickup_latitude',
            'pickup_longitude',
            'pickup_address',
            'dropoff_latitude',
            'dropoff_longitude',
            'dropoff_address',
            'vehicle_type',
            'number_of_passengers',
            'scheduled_time',
            'notes',
        ]
        read_only_fields = ['id']

    def validate_pickup_latitude(self, value):
        """
        Validate that pickup latitude is within valid range.

        Latitude must be between -90 (South Pole) and +90 (North Pole).
        Values outside this range are geographically impossible.

        Args:
            value (float): The latitude value to validate.

        Returns:
            float: The validated latitude.

        Raises:
            serializers.ValidationError: If latitude is out of range.
        """
        if not -90 <= value <= 90:
            raise serializers.ValidationError(
                "Latitude must be between -90 and 90."
            )
        return value

    def validate_pickup_longitude(self, value):
        """
        Validate that pickup longitude is within valid range.

        Longitude must be between -180 (International Date Line, west)
        and +180 (International Date Line, east).

        Args:
            value (float): The longitude value to validate.

        Returns:
            float: The validated longitude.
        """
        if not -180 <= value <= 180:
            raise serializers.ValidationError(
                "Longitude must be between -180 and 180."
            )
        return value

    def validate_dropoff_latitude(self, value):
        """Validate dropoff latitude range (-90 to 90)."""
        if not -90 <= value <= 90:
            raise serializers.ValidationError(
                "Latitude must be between -90 and 90."
            )
        return value

    def validate_dropoff_longitude(self, value):
        """Validate dropoff longitude range (-180 to 180)."""
        if not -180 <= value <= 180:
            raise serializers.ValidationError(
                "Longitude must be between -180 and 180."
            )
        return value

    def validate_number_of_passengers(self, value):
        """
        Validate passenger count is between 1 and 8.

        Most vehicles can't carry more than 8 passengers, and a ride
        with 0 passengers doesn't make sense.

        Args:
            value (int): The number of passengers.

        Returns:
            int: The validated passenger count.
        """
        if value < 1 or value > 8:
            raise serializers.ValidationError(
                "Number of passengers must be between 1 and 8."
            )
        return value

    def validate(self, attrs):
        """
        Object-level validation: ensure pickup and dropoff are different.

        If the pickup and dropoff coordinates are identical (or extremely
        close), the ride doesn't make sense — you can't take a ride to
        the same location you're already at.

        We compare using a small threshold (0.0001 degrees ≈ 11 meters)
        instead of exact equality because GPS coordinates can have tiny
        floating-point differences.

        Args:
            attrs (dict): All validated field values.

        Returns:
            dict: The validated attributes.

        Raises:
            serializers.ValidationError: If pickup equals dropoff.
        """
        pickup_lat = attrs.get('pickup_latitude')
        pickup_lng = attrs.get('pickup_longitude')
        dropoff_lat = attrs.get('dropoff_latitude')
        dropoff_lng = attrs.get('dropoff_longitude')

        # Check if pickup and dropoff are essentially the same point.
        # abs() gives the absolute difference. 0.0001 degrees is about
        # 11 meters at the equator — close enough to be "same place".
        if (abs(pickup_lat - dropoff_lat) < 0.0001 and
                abs(pickup_lng - dropoff_lng) < 0.0001):
            raise serializers.ValidationError(
                "Pickup and dropoff locations must be different."
            )

        return attrs

    def create(self, validated_data):
        """
        Create a new RideRequest with PostGIS Point objects.

        This method is called by serializer.save() after all validations pass.
        It does three things:
          1. Extracts the lat/lng values from validated_data
          2. Converts them into PostGIS Point objects
          3. Creates the RideRequest in the database

        WHY Point(longitude, latitude)?
        PostGIS uses (x, y) coordinate order, where x=longitude and y=latitude.
        This is the OPPOSITE of how we normally say coordinates ("lat, lng").
        Getting this wrong is a VERY common bug that causes rides to appear
        in the wrong location (e.g., in the ocean instead of on land).

        The rider is automatically set from the JWT token (request.user),
        NOT from the request body. This prevents users from creating rides
        on behalf of other users.

        Args:
            validated_data (dict): Clean data after all validations.

        Returns:
            RideRequest: The newly created ride request.
        """
        # Pop the coordinate values — these are NOT model fields, so we
        # can't pass them directly to RideRequest.objects.create().
        pickup_lat = validated_data.pop('pickup_latitude')
        pickup_lng = validated_data.pop('pickup_longitude')
        dropoff_lat = validated_data.pop('dropoff_latitude')
        dropoff_lng = validated_data.pop('dropoff_longitude')

        # Create PostGIS Point objects from the coordinates.
        # Point(x, y) = Point(longitude, latitude) — longitude comes first!
        # srid=4326 tells PostGIS this uses the WGS 84 coordinate system.
        pickup_point = Point(pickup_lng, pickup_lat, srid=4326)
        dropoff_point = Point(dropoff_lng, dropoff_lat, srid=4326)

        # Get the rider from the request context.
        # self.context['request'] is passed automatically by DRF when
        # the serializer is created in the view.
        rider = self.context['request'].user

        # Create the ride request with all validated data.
        ride = RideRequest.objects.create(
            rider=rider,
            pickup_location=pickup_point,
            dropoff_location=dropoff_point,
            **validated_data
        )

        return ride


class RideListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing rides (compact view).

    This serializer is used for list endpoints (GET /api/rides/) where
    we show multiple rides. It includes a subset of fields — just enough
    for a ride card in the mobile app, without heavy data like full
    coordinates or detailed notes.

    COMPUTED FIELDS:
    - rider_username: extracted from the related rider object using
      SerializerMethodField. We show the username instead of just the
      rider ID because the mobile app needs to display who created the ride.
    - pickup_coords / dropoff_coords: extracted from the PostGIS Point
      objects into simple {lat, lng} dictionaries that the mobile app
      can easily use.
    """

    # ---------------------------------------------------------------
    # SerializerMethodField: a read-only field whose value is computed
    # by calling a method named get_<field_name>(). It's not stored in
    # the database — it's calculated on the fly during serialization.
    # ---------------------------------------------------------------
    rider_username = serializers.SerializerMethodField(
        help_text="Username of the rider who created this ride request."
    )

    pickup_coords = serializers.SerializerMethodField(
        help_text="Pickup coordinates as {latitude, longitude}."
    )

    dropoff_coords = serializers.SerializerMethodField(
        help_text="Dropoff coordinates as {latitude, longitude}."
    )

    class Meta:
        model = RideRequest
        fields = [
            'id',
            'rider_username',
            'pickup_address',
            'pickup_coords',
            'dropoff_address',
            'dropoff_coords',
            'vehicle_type',
            'number_of_passengers',
            'status',
            'scheduled_time',
            'created_at',
        ]

    def get_rider_username(self, obj):
        """
        Get the rider's username from the related user object.

        obj is the RideRequest instance being serialized.
        obj.rider is the related CustomUser instance (via ForeignKey).

        Args:
            obj (RideRequest): The ride request being serialized.

        Returns:
            str: The rider's username.
        """
        return obj.rider.username

    def get_pickup_coords(self, obj):
        """
        Extract pickup coordinates from the PostGIS Point object.

        PostGIS Point stores coordinates as (x, y) = (longitude, latitude).
        We return them in a mobile-app-friendly format:
        {"latitude": 17.385, "longitude": 78.4867}

        Args:
            obj (RideRequest): The ride request being serialized.

        Returns:
            dict or None: Coordinate dictionary, or None if no location set.
        """
        if obj.pickup_location:
            return {
                'latitude': obj.pickup_location.y,   # y = latitude
                'longitude': obj.pickup_location.x,  # x = longitude
            }
        return None

    def get_dropoff_coords(self, obj):
        """
        Extract dropoff coordinates from the PostGIS Point object.

        Same logic as get_pickup_coords but for the dropoff location.

        Args:
            obj (RideRequest): The ride request being serialized.

        Returns:
            dict or None: Coordinate dictionary, or None if no location set.
        """
        if obj.dropoff_location:
            return {
                'latitude': obj.dropoff_location.y,
                'longitude': obj.dropoff_location.x,
            }
        return None


class RideDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing a single ride in full detail.

    Used for the ride detail endpoint (GET /api/rides/<id>/) where we show
    ALL information about a ride, including:
    - All fields from the list view
    - Notes, timestamps, and computed properties
    - Whether the ride can still be bid on (is_biddable)
    - Whether the ride is active (is_active)
    - Whether the ride can be cancelled (can_cancel)

    These computed properties help the mobile app determine which action
    buttons to show (e.g., hide the "Place Bid" button if is_biddable=False).
    """

    rider_username = serializers.SerializerMethodField()
    rider_id = serializers.SerializerMethodField()

    pickup_coords = serializers.SerializerMethodField()
    dropoff_coords = serializers.SerializerMethodField()

    # ---------------------------------------------------------------
    # Computed properties from the model — exposed as read-only fields.
    # These use the @property methods we defined on the RideRequest model.
    # SerializerMethodField calls get_<field_name>() which reads the
    # model's @property values.
    # ---------------------------------------------------------------
    is_biddable = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = RideRequest
        fields = [
            'id',
            'rider_id',
            'rider_username',
            'pickup_address',
            'pickup_coords',
            'dropoff_address',
            'dropoff_coords',
            'vehicle_type',
            'number_of_passengers',
            'scheduled_time',
            'notes',
            'status',
            'is_biddable',
            'is_active',
            'can_cancel',
            'created_at',
            'updated_at',
        ]

    def get_rider_username(self, obj):
        """Get the rider's username."""
        return obj.rider.username

    def get_rider_id(self, obj):
        """Get the rider's user ID."""
        return obj.rider.id

    def get_pickup_coords(self, obj):
        """Extract pickup coordinates as {latitude, longitude}."""
        if obj.pickup_location:
            return {
                'latitude': obj.pickup_location.y,
                'longitude': obj.pickup_location.x,
            }
        return None

    def get_dropoff_coords(self, obj):
        """Extract dropoff coordinates as {latitude, longitude}."""
        if obj.dropoff_location:
            return {
                'latitude': obj.dropoff_location.y,
                'longitude': obj.dropoff_location.x,
            }
        return None

    def get_is_biddable(self, obj):
        """
        Check if drivers can still bid on this ride.
        Reads the @property from the RideRequest model.

        Args:
            obj (RideRequest): The ride being serialized.

        Returns:
            bool: True if the ride can accept bids.
        """
        return obj.is_biddable

    def get_is_active(self, obj):
        """
        Check if this ride is still active (not completed/cancelled).

        Args:
            obj (RideRequest): The ride being serialized.

        Returns:
            bool: True if the ride is active.
        """
        return obj.is_active

    def get_can_cancel(self, obj):
        """
        Check if this ride can be cancelled.

        Args:
            obj (RideRequest): The ride being serialized.

        Returns:
            bool: True if the ride can be cancelled.
        """
        return obj.can_cancel


class RideUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a ride request.

    WHAT CAN BE UPDATED:
    Only non-critical fields can be changed after creation:
    - vehicle_type: rider might change their vehicle preference
    - number_of_passengers: rider might add/remove fellow travelers
    - scheduled_time: rider might reschedule
    - notes: rider might add special instructions

    WHAT CANNOT BE UPDATED:
    - Pickup/dropoff locations: changing the route after drivers have seen
      the ride would be unfair to drivers who already bid based on the
      original route.
    - Status: status changes happen through specific action endpoints
      (cancel, accept bid, etc.), not through a generic update.
    - Rider: a ride always belongs to the user who created it.

    RESTRICTIONS:
    - Can only update rides in 'requested' or 'bidding' status.
    - Once a bid is accepted, the ride details are locked.
    """

    class Meta:
        model = RideRequest
        fields = [
            'vehicle_type',
            'number_of_passengers',
            'scheduled_time',
            'notes',
        ]

    def validate_number_of_passengers(self, value):
        """Validate passenger count is between 1 and 8."""
        if value < 1 or value > 8:
            raise serializers.ValidationError(
                "Number of passengers must be between 1 and 8."
            )
        return value

    def validate(self, attrs):
        """
        Ensure the ride is still editable (in 'requested' or 'bidding' status).

        self.instance is the existing RideRequest being updated.
        It's set automatically by DRF when the serializer is initialized
        with an existing object (serializer(instance=ride, data=...)).

        Args:
            attrs (dict): The fields being updated.

        Returns:
            dict: Validated attributes.

        Raises:
            serializers.ValidationError: If the ride can no longer be edited.
        """
        if self.instance and not self.instance.is_biddable:
            raise serializers.ValidationError(
                "This ride can no longer be edited because a bid has been "
                "accepted or the ride has been completed/cancelled."
            )
        return attrs
