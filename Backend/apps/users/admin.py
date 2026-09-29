"""
Django Admin Configuration for the Users app.

WHY CUSTOMIZE THE ADMIN?
------------------------
Django's built-in admin interface provides a powerful UI for managing database
records directly from the browser (at /admin/). However, the default UserAdmin
only knows about the built-in User fields (username, email, password, etc.).

Since we have:
  - Custom fields on User ('role', 'phone', 'profile_picture_url', 'is_verified')
  - Two related models (DriverDetail, RiderDetail) that store role-specific data

...we need to tell the admin interface about ALL of these so they appear in:
  1. The user list page (list_display)
  2. The filter sidebar (list_filter)
  3. The search bar (search_fields)
  4. The user edit form (fieldsets)
  5. The user creation form (add_fieldsets)

We extend Django's built-in UserAdmin class (not plain ModelAdmin) because
UserAdmin has special handling for password hashing, permission management,
and other user-specific functionality that we want to keep.

For DriverDetail and RiderDetail, we use plain ModelAdmin since they don't
need any special user-auth handling.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Import all three of our models.
from .models import User, DriverDetail, RiderDetail


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Admin panel configuration for the User model.

    By using @admin.register(User), this class is automatically
    registered with Django's admin site. This means when you visit
    /admin/, you'll see a "Users" section that uses this configuration.

    We inherit from UserAdmin (not plain admin.ModelAdmin) because UserAdmin
    has built-in support for:
    - Password change forms (shows a password hash, not raw password)
    - Permission checkboxes (is_active, is_staff, is_superuser)
    - Group management
    - Proper user creation flow (asks for password twice)
    """

    # ---------------------------------------------------------------
    # list_display: columns shown on the user list page (/admin/users/user/).
    # Each string is a field name from the model. The admin renders
    # a table with these columns so you can quickly scan all users.
    # ---------------------------------------------------------------
    list_display = ('username', 'email', 'role', 'phone', 'is_verified', 'is_active')

    # ---------------------------------------------------------------
    # list_filter: filter options shown in the right sidebar.
    # Clicking "rider" shows only riders, clicking "driver" shows only drivers.
    # This is extremely useful when you have thousands of users.
    # ---------------------------------------------------------------
    list_filter = ('role', 'is_verified', 'is_active', 'is_staff')

    # ---------------------------------------------------------------
    # search_fields: fields that the search bar at the top of the list
    # page will search through. If an admin types "john", Django will
    # search username, email, and phone for matches.
    # ---------------------------------------------------------------
    search_fields = ('username', 'email', 'phone')

    # ---------------------------------------------------------------
    # fieldsets: defines the layout of the user EDIT form.
    # UserAdmin.fieldsets already includes sections for:
    #   - Personal info (username, first_name, last_name, email)
    #   - Permissions (is_active, is_staff, is_superuser, groups)
    #   - Important dates (last_login, date_joined)
    # We ADD a new "RideBid Info" section at the bottom with our custom fields.
    # The += operator appends to the existing tuple of fieldsets.
    # ---------------------------------------------------------------
    fieldsets = UserAdmin.fieldsets + (
        ('RideBid Info', {
            'fields': ('role', 'phone', 'profile_picture_url', 'is_verified'),
        }),
    )

    # ---------------------------------------------------------------
    # add_fieldsets: defines the layout of the user CREATION form
    # (the form you see when clicking "Add User").
    # UserAdmin.add_fieldsets includes username, password1, password2.
    # We add our custom fields so they can be set during creation.
    # ---------------------------------------------------------------
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('RideBid Info', {
            'fields': ('role', 'phone', 'email'),
        }),
    )


@admin.register(DriverDetail)
class DriverDetailAdmin(admin.ModelAdmin):
    """
    Admin panel configuration for the DriverDetail model.

    This allows admins to:
    - View all driver profiles in a table
    - Approve or reject drivers (toggle is_approved)
    - Search for a driver by their username or email
    - Filter by approval status or vehicle type

    NOTE: DriverDetail has a OneToOne relationship with User.
    Each row in this table belongs to exactly one driver.
    """

    # ---------------------------------------------------------------
    # list_display: these columns are shown in the DriverDetail list view.
    # 'user' will display the string representation of the User
    # (which is "email (role)" as defined in our __str__ method).
    # ---------------------------------------------------------------
    list_display = ('user', 'vehicle_type', 'vehicle_number', 'is_approved', 'is_online', 'rating')

    # ---------------------------------------------------------------
    # list_filter: allows filtering the driver list by these fields.
    # Very useful for finding all unapproved drivers, for example.
    # ---------------------------------------------------------------
    list_filter = ('is_approved', 'is_online', 'vehicle_type')

    # ---------------------------------------------------------------
    # search_fields: the admin search bar will look through these fields.
    # 'user__username' uses Django's double-underscore syntax to traverse
    # the ForeignKey relationship and search the related User's username.
    # ---------------------------------------------------------------
    search_fields = ('user__username', 'user__email', 'license_number', 'vehicle_number')

    # ---------------------------------------------------------------
    # readonly_fields: these fields are shown in the edit form but
    # cannot be changed. 'rating' is computed from completed rides,
    # so admins shouldn't manually set it here.
    # ---------------------------------------------------------------
    readonly_fields = ('rating', 'created_at', 'updated_at')


@admin.register(RiderDetail)
class RiderDetailAdmin(admin.ModelAdmin):
    """
    Admin panel configuration for the RiderDetail model.

    Simpler than DriverDetailAdmin because riders have fewer managed fields.
    Admins mainly use this to look up a rider's rating or home address.
    """

    list_display = ('user', 'rating', 'home_address')

    search_fields = ('user__username', 'user__email')

    # 'rating' is computed from completed rides; admins shouldn't set it manually.
    readonly_fields = ('rating',)
