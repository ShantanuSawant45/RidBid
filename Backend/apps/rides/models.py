"""
Ride Request Model for RideBid.

WHAT IS A RIDE REQUEST?
-----------------------
A ride request is created by a RIDER who needs to go from point A to point B.
It captures:
  - WHERE: pickup and dropoff locations (stored as geographic coordinates)
  - WHEN: scheduled pickup time
  - WHAT: vehicle type preference (auto, mini, sedan, SUV)
  - HOW MANY: number of passengers
  - STATUS: tracks the ride's lifecycle from creation to completion

WHY POSTGIS (Geographic Points)?
---------------------------------
We store locations as PostGIS PointField instead of plain latitude/longitude
floats because PostGIS gives us powerful geospatial queries:
  - "Find all ride requests within 5km of this driver"
  - "Calculate the distance between pickup and dropoff"
  - "Find the nearest available ride to a driver"

These spatial queries use database-level indexing (GiST index) which is
MUCH faster than calculating distances in Python code. For a ride-sharing
app with thousands of concurrent requests, this performance difference
is critical.

RIDE LIFECYCLE (Status Workflow):
  REQUESTED  →  BIDDING  →  ACCEPTED  →  IN_PROGRESS  →  COMPLETED
       │            │            │             │
       └──── CANCELLED ←────────┴─────────────┘

  1. REQUESTED: Rider creates a new ride request
  2. BIDDING: At least one driver has placed a bid (auto-transition)
  3. ACCEPTED: Rider accepted a bid, driver is assigned
  4. IN_PROGRESS: Driver has picked up the rider, trip is ongoing
  5. COMPLETED: Trip finished, rider has been dropped off
  6. CANCELLED: Ride was cancelled (by rider before acceptance, or by system)
"""

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models


class RideRequest(models.Model):
    """
    Represents a ride request created by a rider.

    A rider fills in pickup/dropoff locations, vehicle preference, and
    optionally a scheduled time. Drivers in the area can then see this
    request and place bids with their proposed fare.

    KEY RELATIONSHIPS:
    - rider: the user who created this ride request (ForeignKey to CustomUser)
    - accepted_bid: the bid that was accepted (set when rider chooses a driver)
      This will be a ForeignKey to the Bid model (added in Phase 4).

    COORDINATE SYSTEM:
    All geographic points use SRID 4326 (WGS 84), which is the standard
    coordinate system used by GPS devices and mapping services like Google
    Maps. Coordinates are stored as (longitude, latitude) — note that
    PostGIS uses (x, y) order, which means longitude comes FIRST.
    """

    # =================================================================
    # STATUS CHOICES
    # =================================================================
    # TextChoices creates a Python enum that maps to database values.
    # The first value ('requested') is what gets stored in the database.
    # The second value ('Requested') is the human-readable label.
    # =================================================================
    class Status(models.TextChoices):
        REQUESTED = 'requested', 'Requested'        # Rider just created the ride
        BIDDING = 'bidding', 'Bidding'               # Drivers are placing bids
        ACCEPTED = 'accepted', 'Accepted'            # Rider accepted a bid
        IN_PROGRESS = 'in_progress', 'In Progress'   # Driver picked up rider
        COMPLETED = 'completed', 'Completed'         # Trip finished
        CANCELLED = 'cancelled', 'Cancelled'         # Ride was cancelled

    # =================================================================
    # VEHICLE TYPE CHOICES
    # =================================================================
    # Different vehicle categories that the rider can request.
    # This helps drivers know if the ride matches their vehicle.
    # =================================================================
    class VehicleType(models.TextChoices):
        AUTO = 'auto', 'Auto Rickshaw'      # Three-wheeler auto
        MINI = 'mini', 'Mini (Hatchback)'   # Small car (WagonR, Alto, etc.)
        SEDAN = 'sedan', 'Sedan'            # Mid-size (Swift Dzire, Honda City)
        SUV = 'suv', 'SUV'                  # Large vehicle (Innova, Ertiga)
        ANY = 'any', 'Any Vehicle'          # No preference

    # =================================================================
    # RIDER (who created this ride request)
    # =================================================================
    # ForeignKey creates a many-to-one relationship: one rider can have
    # many ride requests, but each ride request belongs to exactly one rider.
    #
    # on_delete=models.CASCADE: if the rider's account is deleted, all
    # their ride requests are also deleted. This prevents orphaned records.
    #
    # related_name='ride_requests': allows reverse lookup from the user:
    #   user.ride_requests.all()  →  all rides requested by this user
    #
    # settings.AUTH_USER_MODEL: references our CustomUser model indirectly.
    # We use this instead of importing CustomUser directly because Django
    # recommends it — it keeps apps loosely coupled and allows the user
    # model to be swapped without changing this code.
    # =================================================================
    rider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ride_requests',
        help_text="The rider who created this ride request."
    )

    # =================================================================
    # PICKUP LOCATION (where the rider wants to be picked up)
    # =================================================================
    # PointField: a PostGIS geographic field that stores a single point
    # as (longitude, latitude). Under the hood, it stores a WKB (Well-Known
    # Binary) geometry that enables fast spatial indexing and queries.
    #
    # srid=4326: Spatial Reference System Identifier. 4326 = WGS 84,
    # the coordinate system used by GPS. Latitude ranges from -90 to 90,
    # longitude from -180 to 180.
    #
    # geography=True: tells PostGIS to treat this as a geographic point
    # on a sphere (Earth), not a flat plane. This means distance calculations
    # account for Earth's curvature and return results in METERS, not degrees.
    # Without geography=True, a query like "find rides within 5km" would
    # give incorrect results because 1 degree of longitude is ~111km at
    # the equator but ~0km at the poles.
    #
    # spatial_index=True: creates a GiST (Generalized Search Tree) index
    # on this column, making spatial queries like ST_DWithin (find points
    # within a distance) extremely fast — O(log n) instead of O(n).
    # =================================================================
    pickup_location = gis_models.PointField(
        srid=4326,
        geography=True,
        spatial_index=True,
        help_text="Pickup point as (longitude, latitude). Example: POINT(78.4867 17.3850)"
    )

    # Human-readable address string for the pickup location.
    # This is displayed in the UI. The actual coordinates in pickup_location
    # are used for geospatial queries; this is just for display.
    pickup_address = models.CharField(
        max_length=500,
        help_text="Human-readable pickup address. Example: 'Hitech City Metro Station, Hyderabad'"
    )

    # =================================================================
    # DROPOFF LOCATION (where the rider wants to go)
    # =================================================================
    # Same field type and configuration as pickup_location.
    # Having separate spatial indexes on both pickup and dropoff allows
    # efficient queries like:
    #   "Find rides going TO my area" (query on dropoff_location)
    #   "Find rides starting NEAR me" (query on pickup_location)
    # =================================================================
    dropoff_location = gis_models.PointField(
        srid=4326,
        geography=True,
        spatial_index=True,
        help_text="Dropoff point as (longitude, latitude). Example: POINT(78.3810 17.4399)"
    )

    dropoff_address = models.CharField(
        max_length=500,
        help_text="Human-readable dropoff address. Example: 'Gachibowli Stadium, Hyderabad'"
    )

    # =================================================================
    # VEHICLE TYPE PREFERENCE
    # =================================================================
    # The rider's preferred vehicle type. Defaults to 'any' so the rider
    # doesn't have to specify if they don't care.
    # =================================================================
    vehicle_type = models.CharField(
        max_length=10,
        choices=VehicleType.choices,
        default=VehicleType.ANY,
        help_text="Preferred vehicle type for this ride."
    )

    # =================================================================
    # NUMBER OF PASSENGERS
    # =================================================================
    # PositiveSmallIntegerField stores small positive integers (0-32767).
    # We use this instead of IntegerField because passenger count is always
    # a small positive number, and it automatically validates that the
    # value is >= 0.
    # =================================================================
    number_of_passengers = models.PositiveSmallIntegerField(
        default=1,
        help_text="Number of passengers for this ride (1-8)."
    )

    # =================================================================
    # SCHEDULED TIME
    # =================================================================
    # When the rider wants to be picked up. null=True, blank=True makes
    # this optional — if not provided, it means "as soon as possible" (ASAP).
    # =================================================================
    scheduled_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the rider wants to be picked up. Null means ASAP."
    )

    # =================================================================
    # NOTES (optional rider instructions)
    # =================================================================
    # Free-text field for special instructions like "I have luggage",
    # "Please come to Gate 2", "I have a pet", etc.
    # =================================================================
    notes = models.TextField(
        blank=True,
        default='',
        help_text="Optional notes or special instructions for the driver."
    )

    # =================================================================
    # STATUS (ride lifecycle tracking)
    # =================================================================
    # Tracks where the ride is in its lifecycle. See the Status enum above.
    # db_index=True creates a B-tree index on this column for fast filtering
    # (e.g., "show me all rides with status='requested'").
    # =================================================================
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.REQUESTED,
        db_index=True,
        help_text="Current status of the ride in its lifecycle."
    )

    # =================================================================
    # TIMESTAMPS
    # =================================================================
    # auto_now_add=True: sets the field to the current time when the
    #   object is FIRST created. Never changes after that.
    # auto_now=True: updates the field to the current time every time
    #   the object is saved (created or updated).
    # =================================================================
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this ride request was created."
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this ride request was last modified."
    )

    class Meta:
        # ---------------------------------------------------------------
        # db_table: explicit table name instead of auto-generated
        #   'rides_riderequest'.
        # ordering: default sort order for querysets. '-created_at' means
        #   newest rides first (descending). This applies to .all() and
        #   .filter() calls unless overridden with .order_by().
        # indexes: additional database indexes for common query patterns.
        #   These speed up filtering by status and rider.
        # ---------------------------------------------------------------
        db_table = 'ride_requests'
        verbose_name = 'Ride Request'
        verbose_name_plural = 'Ride Requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at'], name='idx_ride_status_created'),
            models.Index(fields=['rider', 'status'], name='idx_ride_rider_status'),
        ]

    def __str__(self):
        """
        String representation shown in admin and shell.
        Example: "Ride #42 by john_doe (requested)"
        """
        return f"Ride #{self.pk} by {self.rider.username} ({self.status})"

    @property
    def is_active(self):
        """
        Check if this ride is still active (can receive bids or is ongoing).

        A ride is active if it's in the 'requested', 'bidding', 'accepted',
        or 'in_progress' state. Completed and cancelled rides are NOT active.

        Returns:
            bool: True if the ride is still active.
        """
        return self.status in (
            self.Status.REQUESTED,
            self.Status.BIDDING,
            self.Status.ACCEPTED,
            self.Status.IN_PROGRESS,
        )

    @property
    def is_biddable(self):
        """
        Check if drivers can still place bids on this ride.

        Only rides in 'requested' or 'bidding' status can accept new bids.
        Once a bid is accepted, no more bids are allowed.

        Returns:
            bool: True if drivers can bid on this ride.
        """
        return self.status in (
            self.Status.REQUESTED,
            self.Status.BIDDING,
        )

    @property
    def can_cancel(self):
        """
        Check if this ride can be cancelled.

        A ride can only be cancelled if no driver has started the trip yet.
        Once a ride is in_progress, completed, or already cancelled,
        it cannot be cancelled.

        Returns:
            bool: True if the ride can be cancelled.
        """
        return self.status in (
            self.Status.REQUESTED,
            self.Status.BIDDING,
            self.Status.ACCEPTED,
        )
