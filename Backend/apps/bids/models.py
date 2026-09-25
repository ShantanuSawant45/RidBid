"""
Models for the Bids app.

WHAT IS A BID?
--------------
When a Rider creates a RideRequest, Drivers in the area can view it and
offer to take the ride for a specific price. This offer is a "Bid".

BID LIFECYCLE:
  PENDING   → The driver placed the bid, waiting for rider's decision.
  ACCEPTED  → The rider accepted this bid. The driver won the ride.
  REJECTED  → The rider accepted a DIFFERENT bid, or explicitly rejected this one.
  CANCELLED → The driver withdrew their bid before the rider made a decision.

RELATIONSHIPS:
- ride (ForeignKey to RideRequest): Which ride is this bid for?
- driver (ForeignKey to CustomUser): Which driver placed this bid?

By keeping Bids in a separate app from Rides, we follow the Django
principle of loosely coupled, highly cohesive apps.
"""

from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator

class Bid(models.Model):
    """
    Represents an offer made by a driver to fulfill a ride request.
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
        CANCELLED = 'cancelled', 'Cancelled'

    # =================================================================
    # RELATIONSHIPS
    # =================================================================
    # We reference the RideRequest model using a string 'rides.RideRequest'
    # instead of importing it directly to avoid circular import issues.
    ride = models.ForeignKey(
        'rides.RideRequest',
        on_delete=models.CASCADE,
        related_name='bids',
        help_text="The ride request this bid is for."
    )

    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bids_placed',
        help_text="The driver who placed this bid."
    )

    # =================================================================
    # BID DETAILS
    # =================================================================
    # DecimalField is used for currency to avoid floating point precision errors.
    # max_digits=8 and decimal_places=2 allows values up to 999999.99
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(1.00)],
        help_text="The proposed fare amount for the ride."
    )

    # Optional ETA in minutes provided by the driver
    estimated_arrival_time = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Estimated time of arrival at the pickup location (in minutes)."
    )

    # =================================================================
    # STATUS & TIMESTAMPS
    # =================================================================
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        help_text="Current status of this bid."
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this bid was placed."
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this bid was last modified."
    )

    class Meta:
        db_table = 'bids'
        verbose_name = 'Bid'
        verbose_name_plural = 'Bids'
        ordering = ['amount', 'created_at']  # Order by lowest price first, then oldest
        
        # A driver should only be able to place one active bid per ride
        # We enforce this at the database level using a UniqueConstraint
        constraints = [
            models.UniqueConstraint(
                fields=['ride', 'driver'],
                condition=models.Q(status='pending'),
                name='unique_pending_bid_per_driver'
            )
        ]

    def __str__(self):
        """String representation for admin and shell."""
        return f"Bid #{self.pk} by {self.driver.username} for Ride #{self.ride_id} (₹{self.amount})"
