from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models


class Status(models.TextChoices):
    REQUESTED = 'requested', 'Requested'
    BIDDING = 'bidding', 'Bidding'
    ACCEPTED = 'accepted', 'Accepted'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'

class VehicleType(models.TextChoices):
    AUTO = 'auto', 'Auto Rickshaw'
    MINI = 'mini', 'Mini (Hatchback)'
    SEDAN = 'sedan', 'Sedan'
    SUV = 'suv', 'SUV'
    ANY = 'any', 'Any Vehicle'


class RideRequest(models.Model):

    rider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ride_requests',
        help_text="The rider who created this ride request."
    )

    pickup_location = gis_models.PointField(
        srid=4326,
        geography=True,
        spatial_index=True,
        help_text="Pickup point as (longitude, latitude). Example: POINT(78.4867 17.3850)"
    )

    pickup_address = models.CharField(
        max_length=500,
        help_text="Human-readable pickup address. Example: 'Hitech City Metro Station, Hyderabad'"
    )

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

    vehicle_type = models.CharField(
        max_length=10,
        choices=VehicleType.choices,
        default=VehicleType.ANY,
        help_text="Preferred vehicle type for this ride."
    )

    number_of_passengers = models.PositiveSmallIntegerField(
        default=1,
        help_text="Number of passengers for this ride (1-8)."
    )

    scheduled_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the rider wants to be picked up. Null means ASAP."
    )

    notes = models.TextField(
        blank=True,
        default='',
        help_text="Optional notes or special instructions for the driver."
    )

    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.REQUESTED,
        db_index=True,
        help_text="Current status of the ride in its lifecycle."
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this ride request was created."
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this ride request was last modified."
    )

    class Meta:
        db_table = 'ride_requests'
        verbose_name = 'Ride Request'
        verbose_name_plural = 'Ride Requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at'], name='idx_ride_status_created'),
            models.Index(fields=['rider', 'status'], name='idx_ride_rider_status'),
        ]

    def __str__(self):
        return f"Ride #{self.pk} by {self.rider.username} ({self.status})"

    @property
    def is_active(self):
        return self.status in (
            Status.REQUESTED,
            Status.BIDDING,
            Status.ACCEPTED,
            Status.IN_PROGRESS,
        )

    @property
    def is_biddable(self):
        return self.status in (
            Status.REQUESTED,
            Status.BIDDING,
        )

    @property
    def can_cancel(self):
        return self.status in (
            Status.REQUESTED,
            Status.BIDDING,
            Status.ACCEPTED,
        )
