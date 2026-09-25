"""
URL routing for the Bids app.

These URLs map to the views that handle bidding actions.
Mounted at /api/bids/ by config/urls.py.
"""

from django.urls import path

from .views import (
    BidCreateView,
    BidListView,
    BidAcceptView,
    BidCancelView,
)

app_name = 'bids'

urlpatterns = [
    # POST /api/bids/
    path(
        '',
        BidCreateView.as_view(),
        name='bid-create'
    ),
    
    # GET /api/bids/
    path(
        '',
        BidListView.as_view(),
        name='bid-list'
    ),

    # POST /api/bids/<id>/accept/
    path(
        '<int:bid_id>/accept/',
        BidAcceptView.as_view(),
        name='bid-accept'
    ),

    # POST /api/bids/<id>/cancel/
    path(
        '<int:bid_id>/cancel/',
        BidCancelView.as_view(),
        name='bid-cancel'
    ),
]
