"""
Custom Permission Classes for RideBid.

WHAT ARE PERMISSIONS?
---------------------
Permissions control WHO can access WHICH API endpoints. They run AFTER
authentication (which verifies "who are you?") and answer the question
"are you ALLOWED to do this?"

Django REST Framework's permission system works in two stages:
  1. has_permission(request, view): Called BEFORE any view logic runs.
     Decides if the user can access this endpoint AT ALL.
  2. has_object_permission(request, view, obj): Called for detail views.
     Decides if the user can access THIS SPECIFIC object.

If any permission check returns False, DRF immediately returns a
403 Forbidden response without executing the view code.

BUILT-IN PERMISSIONS WE USE:
- IsAuthenticated: user must be logged in (have a valid JWT token)
- AllowAny: anyone can access (used for registration/login)

CUSTOM PERMISSIONS WE DEFINE:
- IsRider        : users with role='rider' OR 'rider_driver' can access
- IsDriver       : users with role='driver' OR 'rider_driver' can access
- IsRiderOrDriver: any logged-in user (all roles allowed) — useful for
                   endpoints that both riders and drivers need
- IsOwnerOrReadOnly: users can only edit their own data

WHY INCLUDE 'rider_driver' IN BOTH IsRider AND IsDriver?
A rider_driver user registered as both a rider and a driver. They should be
able to use BOTH rider features (requesting rides) and driver features
(bidding on rides). So IsRider and IsDriver both include 'rider_driver'.
"""

from rest_framework.permissions import BasePermission

# Import the Role choices to avoid hardcoding strings like 'rider'.
# Using the enum means if we ever rename a role, we only change it in models.py.
from .models import Role


class IsRider(BasePermission):
    """
    Permission that allows access ONLY to users who can act as a rider.

    ALLOWED ROLES: 'rider' and 'rider_driver'
    DENIED ROLES: 'driver' (a driver-only user cannot request rides)

    USE CASE:
    Only riders should be able to create ride requests. A driver-only user
    shouldn't be able to create a ride request because they're supposed to
    BID on ride requests, not create them.

    HOW IT'S USED:
    In a view, set: permission_classes = [IsAuthenticated, IsRider]
    This means: user must be logged in AND be a rider (or rider_driver).

    WHAT HAPPENS IF DENIED:
    DRF returns HTTP 403 Forbidden with the message defined in 'message'.
    """

    # This message is returned in the API response when permission is denied.
    message = "Only riders can perform this action."

    def has_permission(self, request, view):
        """
        Check if the authenticated user has a rider-compatible role.

        'rider_driver' users are included because they can also request rides.

        Args:
            request: The incoming HTTP request. request.user is the
                authenticated user (decoded from the JWT token).
            view: The view class/function being accessed.

        Returns:
            bool: True if the user is a rider or rider_driver, False otherwise.
        """
        return (
            request.user
            and request.user.is_authenticated
            # Check if the user's role is in the set of rider-compatible roles.
            and request.user.role in (Role.RIDER, Role.RIDER_DRIVER)
        )


class IsDriver(BasePermission):
    """
    Permission that allows access ONLY to users who can act as a driver.

    ALLOWED ROLES: 'driver' and 'rider_driver'
    DENIED ROLES: 'rider' (a rider-only user cannot place bids on rides)

    USE CASE:
    Only drivers should be able to place bids on ride requests.
    A rider-only user shouldn't be able to bid because they're the ones
    requesting the ride.

    HOW IT'S USED:
    In a view, set: permission_classes = [IsAuthenticated, IsDriver]
    This means: user must be logged in AND be a driver (or rider_driver).
    """

    message = "Only drivers can perform this action."

    def has_permission(self, request, view):
        """
        Check if the authenticated user has a driver-compatible role.

        Args:
            request: The incoming HTTP request.
            view: The view being accessed.

        Returns:
            bool: True if the user is a driver or rider_driver, False otherwise.
        """
        return (
            request.user
            and request.user.is_authenticated
            # Both 'driver' and 'rider_driver' roles can act as a driver.
            and request.user.role in (Role.DRIVER, Role.RIDER_DRIVER)
        )


class IsRiderOrDriver(BasePermission):
    """
    Permission that allows access to ANY authenticated user regardless of role.

    This exists for endpoints where both riders and drivers are valid
    users — for example, viewing their own profile or changing their password.
    It's semantically clearer than using just IsAuthenticated in places
    where we want to be explicit that "both roles are welcome here".

    In practice, this is equivalent to IsAuthenticated, but naming it
    IsRiderOrDriver makes the intent clear at the view level.
    """

    message = "You must be a registered user to perform this action."

    def has_permission(self, request, view):
        """
        Allow access to any authenticated user with a valid role.

        Args:
            request: The incoming HTTP request.
            view: The view being accessed.

        Returns:
            bool: True if the user is authenticated, False otherwise.
        """
        return (
            request.user
            and request.user.is_authenticated
            # All three roles are valid
            and request.user.role in (Role.RIDER, Role.DRIVER, Role.RIDER_DRIVER)
        )


class IsOwnerOrReadOnly(BasePermission):
    """
    Permission that allows users to edit ONLY their own data.

    This is an OBJECT-LEVEL permission. It's checked when a view tries
    to access a specific object (like a specific user's profile).

    RULES:
    - Safe methods (GET, HEAD, OPTIONS) are allowed for anyone who is
      authenticated. "Safe" means they don't modify data.
    - Unsafe methods (PUT, PATCH, DELETE) are allowed ONLY if the object
      being modified belongs to the requesting user.

    EXAMPLE:
    - User "john" sends GET /api/users/profile/ → allowed (safe method)
    - User "john" sends PATCH /api/users/5/profile/ where 5 is john's ID
      → allowed (john is the owner)
    - User "john" sends PATCH /api/users/10/profile/ where 10 is jane's ID
      → DENIED (john is not the owner)

    This prevents users from modifying each other's profiles.
    """

    message = "You can only modify your own data."

    def has_object_permission(self, request, view, obj):
        """
        Check if the user owns the object they're trying to modify.

        This method is called by DRF when a view calls self.get_object().
        It's NOT called for list views (which don't target a specific object).

        Args:
            request: The incoming HTTP request.
            view: The view being accessed.
            obj: The specific database object being accessed. For user
                profiles, this is a User instance.

        Returns:
            bool: True if the request is safe (read-only) or if the user
                owns the object. False otherwise.
        """
        # SAFE_METHODS is a tuple: ('GET', 'HEAD', 'OPTIONS')
        # These methods don't modify data, so we allow them for anyone
        # who passed the authentication check.
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True

        # For unsafe methods (PUT, PATCH, DELETE), check if the object
        # being modified is the same user making the request.
        # obj == request.user compares the user IDs.
        return obj == request.user
