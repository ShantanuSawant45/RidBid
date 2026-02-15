"""
API Views for the Bids app.

WHAT THESE VIEWS DO:
--------------------
These views handle the bidding workflow:
  1. Drivers place bids on available rides.
  2. Riders view bids on their rides.
  3. Riders accept a bid (which assigns the driver and rejects other bids).
  4. Drivers can cancel their bids.

VIEWS IN THIS FILE:
  - BidCreateView: POST /api/bids/
  - BidListView: GET /api/bids/?ride_id=5
  - BidAcceptView: POST /api/bids/<id>/accept/
  - BidCancelView: POST /api/bids/<id>/cancel/
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from apps.users.permissions import IsRider, IsDriver
from apps.rides.models import RideRequest
from .models import Bid
from .serializers import (
    BidCreateSerializer,
    BidListSerializer,
    BidDetailSerializer,
)


class BidCreateView(APIView):
    """
    API endpoint for drivers to place a bid on a ride.

    URL: POST /api/bids/
    Authentication: Required
    Permission: Drivers only
    """
    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request):
        serializer = BidCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        bid = serializer.save()
        bid_data = BidDetailSerializer(bid).data

        # ---------------------------------------------------------------
        # Phase 5: Real-time update
        # Send the new bid to the rider via WebSocket.
        # ---------------------------------------------------------------
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'ride_{bid.ride_id}',
            {
                'type': 'bid.placed',    # Triggers bid_placed() in consumer
                'bid_data': bid_data
            }
        )

        # ---------------------------------------------------------------
        # Phase 6: Background Tasks
        # Schedule this bid to auto-expire in 5 minutes (300 seconds)
        # if the rider doesn't accept it.
        # ---------------------------------------------------------------
        from apps.tasks.tasks import expire_bid
        expire_bid.apply_async(args=[bid.id], countdown=300)

        return Response(
            {
                'message': 'Bid placed successfully.',
                'bid': bid_data,
            },
            status=status.HTTP_201_CREATED
        )


class BidListView(APIView):
    """
    API endpoint for listing bids.

    URL: GET /api/bids/
    Authentication: Required
    Permission: Any authenticated user

    - If Rider: must provide ?ride_id=X to see bids on their specific ride.
    - If Driver: sees all bids they have placed.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.is_rider:
            # Rider wants to see bids for a specific ride they created
            ride_id = request.query_params.get('ride_id')
            if not ride_id:
                return Response(
                    {'error': 'Riders must provide a ride_id query parameter.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Security check: ensure the rider owns this ride
            try:
                ride = RideRequest.objects.get(pk=ride_id, rider=user)
            except RideRequest.DoesNotExist:
                return Response(
                    {'error': 'Ride not found or you do not have permission to view its bids.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            bids = Bid.objects.filter(ride=ride).select_related('driver')
        
        else:
            # Driver wants to see their own bids
            bids = Bid.objects.filter(driver=user).select_related('ride')
            
            # Optional filter by ride_id for drivers too
            ride_id = request.query_params.get('ride_id')
            if ride_id:
                bids = bids.filter(ride_id=ride_id)

        serializer = BidListSerializer(bids, many=True)
        return Response(
            {
                'count': bids.count(),
                'bids': serializer.data,
            },
            status=status.HTTP_200_OK
        )


class BidAcceptView(APIView):
    """
    API endpoint for a rider to accept a bid.

    URL: POST /api/bids/<id>/accept/
    Authentication: Required
    Permission: Riders only

    WHAT HAPPENS WHEN ACCEPTED:
    1. The accepted bid's status changes to ACCEPTED.
    2. All other pending bids for this ride change to REJECTED.
    3. The RideRequest's status changes to ACCEPTED.
    4. (Optional) We could set a ForeignKey on RideRequest pointing to the accepted bid.
    """
    permission_classes = [IsAuthenticated, IsRider]

    def post(self, request, bid_id):
        try:
            bid = Bid.objects.select_related('ride').get(pk=bid_id)
        except Bid.DoesNotExist:
            return Response(
                {'error': 'Bid not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        ride = bid.ride

        # Security check: only the rider who created the ride can accept bids
        if ride.rider != request.user:
            return Response(
                {'error': 'You can only accept bids on your own rides.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Business logic: ride must be biddable and bid must be pending
        if not ride.is_biddable:
            return Response(
                {'error': 'This ride is no longer accepting bids.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if bid.status != Bid.Status.PENDING:
            return Response(
                {'error': 'Can only accept pending bids.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ---------------------------------------------------------------
        # Use transaction.atomic() to ensure all database updates succeed 
        # together, or none of them do. If an error occurs midway, 
        # everything rolls back.
        # ---------------------------------------------------------------
        with transaction.atomic():
            # 1. Update the winning bid
            bid.status = Bid.Status.ACCEPTED
            bid.save(update_fields=['status', 'updated_at'])

            # 2. Update all other pending bids for this ride to REJECTED
            Bid.objects.filter(
                ride=ride, 
                status=Bid.Status.PENDING
            ).exclude(pk=bid.pk).update(status=Bid.Status.REJECTED)

            # 3. Update the ride status
            ride.status = RideRequest.Status.ACCEPTED
            ride.save(update_fields=['status', 'updated_at'])

        bid_data = BidDetailSerializer(bid).data

        # Phase 5: Real-time update
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'ride_{ride.id}',
            {
                'type': 'bid.accepted',
                'bid_data': bid_data
            }
        )

        return Response(
            {
                'message': 'Bid accepted successfully. The driver has been assigned to your ride.',
                'bid': bid_data,
            },
            status=status.HTTP_200_OK
        )


class BidCancelView(APIView):
    """
    API endpoint for a driver to cancel their bid.

    URL: POST /api/bids/<id>/cancel/
    Authentication: Required
    Permission: Drivers only
    """
    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request, bid_id):
        try:
            bid = Bid.objects.select_related('ride').get(pk=bid_id)
        except Bid.DoesNotExist:
            return Response(
                {'error': 'Bid not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Security check
        if bid.driver != request.user:
            return Response(
                {'error': 'You can only cancel your own bids.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Business logic
        if bid.status != Bid.Status.PENDING:
            return Response(
                {'error': 'You can only cancel pending bids.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Cancel the bid
        bid.status = Bid.Status.CANCELLED
        bid.save(update_fields=['status', 'updated_at'])
        
        bid_data = BidDetailSerializer(bid).data

        # Phase 5: Real-time update
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'ride_{bid.ride_id}',
            {
                'type': 'bid.cancelled',
                'bid_data': bid_data
            }
        )

        return Response(
            {
                'message': 'Bid cancelled successfully.',
                'bid': bid_data,
            },
            status=status.HTTP_200_OK
        )
