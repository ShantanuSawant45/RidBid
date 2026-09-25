"""
Serializers for the Bids app.

WHAT THESE SERIALIZERS DO:
--------------------------
These serializers handle the conversion of Bid model instances to and from JSON.

SERIALIZERS IN THIS FILE:
  1. BidCreateSerializer: handles creating a new bid by a driver
  2. BidListSerializer: handles listing bids (compact view for riders/drivers)
  3. BidDetailSerializer: handles full details of a bid
"""

from rest_framework import serializers

from apps.rides.models import RideRequest
from .models import Bid


class BidCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for placing a new bid.

    WHAT THE CLIENT SENDS (JSON):
    {
        "ride_id": 5,
        "amount": 150.00,
        "estimated_arrival_time": 10
    }
    """
    
    # We accept ride_id in the payload, but it maps to the 'ride' ForeignKey
    ride_id = serializers.PrimaryKeyRelatedField(
        queryset=RideRequest.objects.all(),
        source='ride',
        help_text="The ID of the ride request being bid on."
    )

    class Meta:
        model = Bid
        fields = [
            'id',
            'ride_id',
            'amount',
            'estimated_arrival_time',
        ]
        read_only_fields = ['id']

    def validate_ride_id(self, value):
        """
        Validate that the ride is open for bidding.

        Args:
            value (RideRequest): The ride object resolved by PrimaryKeyRelatedField.
            
        Returns:
            RideRequest: The validated ride object.
        """
        if not value.is_biddable:
            raise serializers.ValidationError(
                "This ride is no longer accepting bids."
            )
        return value

    def validate(self, attrs):
        """
        Object-level validation.
        Ensure the driver hasn't already placed an active bid on this ride.
        """
        ride = attrs.get('ride')
        driver = self.context['request'].user

        # Check if this driver already has a pending bid for this ride
        if Bid.objects.filter(ride=ride, driver=driver, status=Bid.Status.PENDING).exists():
            raise serializers.ValidationError(
                "You already have a pending bid for this ride. Cancel it before placing a new one."
            )

        return attrs

    def create(self, validated_data):
        """
        Create the bid and auto-assign the driver from the request.
        """
        driver = self.context['request'].user
        
        # validated_data already has 'ride' resolved into a RideRequest object
        bid = Bid.objects.create(
            driver=driver,
            **validated_data
        )
        
        # When a first bid is placed, if the ride is still 'requested', 
        # it should transition to 'bidding'.
        ride = bid.ride
        if ride.status == RideRequest.Status.REQUESTED:
            ride.status = RideRequest.Status.BIDDING
            ride.save(update_fields=['status', 'updated_at'])

        return bid


class BidListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing bids.
    Used by riders to view incoming bids, and drivers to see their own bids.
    """
    
    driver_username = serializers.SerializerMethodField()
    
    class Meta:
        model = Bid
        fields = [
            'id',
            'ride_id',
            'driver_username',
            'amount',
            'estimated_arrival_time',
            'status',
            'created_at',
        ]

    def get_driver_username(self, obj):
        return obj.driver.username


class BidDetailSerializer(serializers.ModelSerializer):
    """
    Full detail serializer for a bid.
    """
    
    driver_username = serializers.SerializerMethodField()
    driver_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Bid
        fields = [
            'id',
            'ride_id',
            'driver_id',
            'driver_username',
            'amount',
            'estimated_arrival_time',
            'status',
            'created_at',
            'updated_at',
        ]

    def get_driver_username(self, obj):
        return obj.driver.username

    def get_driver_id(self, obj):
        return obj.driver.id
