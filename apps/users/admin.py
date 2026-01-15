"""
Django Admin Configuration for CustomUser.

WHY CUSTOMIZE THE ADMIN?
------------------------
Django's built-in admin interface provides a powerful UI for managing database
records directly from the browser (at /admin/). However, the default UserAdmin
only knows about the built-in User fields (username, email, password, etc.).

Since we added custom fields ('role' and 'phone_number') to our CustomUser model,
we need to tell the admin interface about these fields so they appear in:
  1. The user list page (list_display)
  2. The filter sidebar (list_filter)
  3. The search bar (search_fields)
  4. The user edit form (fieldsets)
  5. The user creation form (add_fieldsets)

We extend Django's built-in UserAdmin class (not plain ModelAdmin) because
UserAdmin has special handling for password hashing, permission management,
and other user-specific functionality that we want to keep.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Admin panel configuration for the CustomUser model.

    By using @admin.register(CustomUser), this class is automatically
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
    # list_display: columns shown on the user list page (/admin/users/customuser/).
    # Each string is a field name from the model. The admin renders
    # a table with these columns so you can quickly scan all users.
    # ---------------------------------------------------------------
    list_display = ('username', 'email', 'role', 'phone_number', 'is_active')

    # ---------------------------------------------------------------
    # list_filter: filter options shown in the right sidebar.
    # Clicking "rider" shows only riders, clicking "driver" shows only drivers.
    # This is extremely useful when you have thousands of users.
    # ---------------------------------------------------------------
    list_filter = ('role', 'is_active', 'is_staff')

    # ---------------------------------------------------------------
    # search_fields: fields that the search bar at the top of the list
    # page will search through. If an admin types "john", Django will
    # search username, email, and phone_number for matches.
    # ---------------------------------------------------------------
    search_fields = ('username', 'email', 'phone_number')

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
            'fields': ('role', 'phone_number'),
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
            'fields': ('role', 'phone_number'),
        }),
    )
