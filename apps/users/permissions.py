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
- IsRider: only users with role='rider' can access
- IsDriver: only users with role='driver' can access
- IsOwnerOrReadOnly: users can only edit their own data
"""

from rest_framework.permissions import BasePermission


class IsRider(BasePermission):
    """
    Permission that allows access ONLY to users with role='rider'.

    USE CASE:
    Only riders should be able to create ride requests. A driver shouldn't
    be able to create a ride request because they're supposed to BID on
    ride requests, not create them.

    HOW IT'S USED:
    In a view, set: permission_classes = [IsAuthenticated, IsRider]
    This means: user must be logged in AND be a rider.

    WHAT HAPPENS IF DENIED:
    DRF returns HTTP 403 Forbidden with the message defined in 'message'.
    """

    # This message is returned in the API response when permission is denied.
    message = "Only riders can perform this action."

    def has_permission(self, request, view):
        """
        Check if the authenticated user has the 'rider' role.

        This method is called automatically by DRF before the view
        function/method runs. If it returns False, the view code
        never executes and DRF returns a 403 response.

        Args:
            request: The incoming HTTP request. request.user is the
                authenticated user (decoded from the JWT token).
            view: The view class/function being accessed.

        Returns:
            bool: True if the user is a rider, False otherwise.
        """
        # request.user.is_authenticated checks that the user is logged in
        # (not an anonymous user). request.user.is_rider uses our custom
        # property from the CustomUser model.
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_rider
        )


class IsDriver(BasePermission):
    """
    Permission that allows access ONLY to users with role='driver'.

    USE CASE:
    Only drivers should be able to place bids on ride requests.
    A rider shouldn't be able to bid because they're the ones
    requesting the ride.

    HOW IT'S USED:
    In a view, set: permission_classes = [IsAuthenticated, IsDriver]
    This means: user must be logged in AND be a driver.
    """

    message = "Only drivers can perform this action."

    def has_permission(self, request, view):
        """
        Check if the authenticated user has the 'driver' role.

        Args:
            request: The incoming HTTP request.
            view: The view being accessed.

        Returns:
            bool: True if the user is a driver, False otherwise.
        """
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_driver
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
                profiles, this is a CustomUser instance.

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
