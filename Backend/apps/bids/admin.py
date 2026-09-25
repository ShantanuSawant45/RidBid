"""
Django Admin Configuration for the Bids app.
"""

from django.contrib import admin
from .models import Bid

@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'ride_id',
        'driver',
        'amount',
        'status',
        'created_at',
    ]
    
    list_filter = [
        'status',
        'created_at',
    ]
    
    search_fields = [
        'driver__username',
        'ride__id',
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    list_per_page = 25
