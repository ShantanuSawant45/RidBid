"""
Celery Background Tasks.

WHAT ARE BACKGROUND TASKS?
--------------------------
Normally, when an HTTP request comes in, the server processes it and sends a response.
If the server has to do something time-consuming (like sending an email or generating
a report), the user has to wait for it to finish before getting the response.

Celery solves this by moving work to a background worker process. The HTTP view
says "Hey Celery, do this thing later", and immediately returns a fast response
to the user.

In this file, we define tasks for:
1. Auto-expiring stale bids (e.g., cancelling a bid if it's been pending for 5 mins)
2. Auto-expiring stale rides (e.g., cancelling a ride if no one accepts it in 15 mins)

HOW IT WORKS:
We use Celery's `apply_async(countdown=300)` feature. When a bid is created,
we schedule `expire_bid` to run 300 seconds (5 mins) later. When 5 mins pass,
the Celery worker wakes up, checks if the bid is STILL pending, and if so,
cancels it.
"""

from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from apps.rides.models import RideRequest
from apps.bids.models import Bid
from apps.bids.serializers import BidDetailSerializer
from apps.rides.serializers import RideDetailSerializer

@shared_task
def expire_bid(bid_id):
    """
    Task to auto-expire a bid if it has been pending for too long.
    
    Args:
        bid_id (int): The ID of the bid to check and potentially expire.
    """
    try:
        # We must refetch the bid from the database to get its CURRENT state,
        # not the state it was in when the task was scheduled.
        bid = Bid.objects.select_related('ride').get(pk=bid_id)
    except Bid.DoesNotExist:
        return f"Bid {bid_id} no longer exists."

    # Only expire if it is still PENDING.
    # If the rider already accepted it, or the driver cancelled it, do nothing.
    if bid.status == Bid.Status.PENDING:
        bid.status = Bid.Status.CANCELLED
        bid.save(update_fields=['status', 'updated_at'])

        # Notify the rider via WebSocket that the bid expired
        bid_data = BidDetailSerializer(bid).data
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'ride_{bid.ride_id}',
            {
                'type': 'bid.cancelled',
                'bid_data': bid_data,
                'message': 'Bid automatically expired due to timeout.'
            }
        )
        return f"Bid {bid_id} was successfully auto-expired."

    return f"Bid {bid_id} is already in status {bid.status}, skipping expiry."


@shared_task
def expire_ride(ride_id):
    """
    Task to auto-expire a ride request if it hasn't been accepted in time.
    
    Args:
        ride_id (int): The ID of the ride to check and potentially expire.
    """
    try:
        ride = RideRequest.objects.get(pk=ride_id)
    except RideRequest.DoesNotExist:
        return f"Ride {ride_id} no longer exists."

    # A ride is stale if it hasn't been ACCEPTED or COMPLETED.
    # We check if it is still in a biddable state.
    if ride.is_biddable:
        # Cancel the ride
        ride.status = RideRequest.Status.CANCELLED
        ride.save(update_fields=['status', 'updated_at'])

        # Also cancel any pending bids for this ride so drivers get their slots back
        Bid.objects.filter(
            ride=ride, 
            status=Bid.Status.PENDING
        ).update(status=Bid.Status.CANCELLED)

        # Notify the rider that their ride timed out
        # (Though they probably know since their app will check status)
        return f"Ride {ride_id} was successfully auto-expired."

    return f"Ride {ride_id} is already in status {ride.status}, skipping expiry."
