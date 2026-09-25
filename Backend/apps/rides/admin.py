"""
Django Admin Configuration for the Rides app.

WHAT IS DJANGO ADMIN?
---------------------
Django Admin is a built-in web interface that lets you view, create, edit,
and delete database records without writing any frontend code. It's accessed
at /admin/ and is extremely useful during development for:
  - Inspecting ride data in the database
  - Manually changing ride statuses for testing
  - Debugging issues by looking at actual data

This file customizes how the RideRequest model appears in the admin panel.
Without customization, the admin would just show a list of "Ride Request object (1)",
"Ride Request object (2)", etc. — not very useful! With customization, we get
a rich table with filters, search, and nicely formatted columns.
"""

from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import RideRequest


@admin.register(RideRequest)
class RideRequestAdmin(GISModelAdmin):
    """
    Admin configuration for the RideRequest model.

    GISModelAdmin (instead of ModelAdmin) adds an interactive MAP widget
    for PointField fields. This lets you visually see and edit the pickup
    and dropoff locations on a map in the admin panel.

    KEY CUSTOMIZATIONS:
    - list_display: columns shown in the list view
    - list_filter: sidebar filters for quick filtering
    - search_fields: fields searchable via the search box
    - readonly_fields: fields that can't be edited in the admin
    - fieldsets: organize edit form into logical sections
    """

    # ---------------------------------------------------------------
    # list_display: columns shown in the ride list table.
    # Each string is either a model field name or a method name.
    # The admin renders each as a column in the list view.
    # ---------------------------------------------------------------
    list_display = [
        'id',
        'rider',
        'pickup_address',
        'dropoff_address',
        'vehicle_type',
        'status',
        'number_of_passengers',
        'created_at',
    ]

    # ---------------------------------------------------------------
    # list_filter: sidebar filters.
    # Clicking a filter value instantly filters the list.
    # Example: click "Requested" under Status to see only requested rides.
    # ---------------------------------------------------------------
    list_filter = [
        'status',
        'vehicle_type',
        'created_at',
    ]

    # ---------------------------------------------------------------
    # search_fields: fields that are searched when you type in the
    # admin search box. Uses SQL LIKE for text fields.
    # 'rider__username' searches across the ForeignKey relationship
    # (looks at the rider's username).
    # ---------------------------------------------------------------
    search_fields = [
        'pickup_address',
        'dropoff_address',
        'rider__username',
    ]

    # ---------------------------------------------------------------
    # readonly_fields: fields that appear in the detail/edit form but
    # cannot be modified. created_at and updated_at are auto-managed
    # by Django and should never be manually edited.
    # ---------------------------------------------------------------
    readonly_fields = ['created_at', 'updated_at']

    # ---------------------------------------------------------------
    # fieldsets: organize the edit form into logical sections.
    # Each tuple is (section_title, {fields: [...]}).
    # This makes the form easier to understand for admins.
    # ---------------------------------------------------------------
    fieldsets = (
        ('Ride Info', {
            'fields': ('rider', 'status', 'vehicle_type', 'number_of_passengers')
        }),
        ('Pickup', {
            'fields': ('pickup_location', 'pickup_address')
        }),
        ('Dropoff', {
            'fields': ('dropoff_location', 'dropoff_address')
        }),
        ('Schedule & Notes', {
            'fields': ('scheduled_time', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),  # Collapsed by default to save space
        }),
    )

    # ---------------------------------------------------------------
    # list_per_page: how many rides to show per page in the list view.
    # 25 is a good balance between seeing enough data and page load speed.
    # ---------------------------------------------------------------
    list_per_page = 25
