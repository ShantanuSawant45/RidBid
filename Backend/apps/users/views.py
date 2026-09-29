
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

# Import our models and serializers.
from .models import User, DriverDetail, RiderDetail, Role
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    DriverDetailSerializer,
    RiderDetailSerializer,
    ChangePasswordSerializer,
)
# Import our custom role-based permission classes.
from .permissions import IsDriver, IsRider, IsRiderOrDriver


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        return Response(
            {
                'message': 'Registration successful.',
                'user': UserProfileSerializer(user).data,
                'tokens': tokens,
            },
            status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    """
    API endpoint for user login (authentication).

    URL: POST /api/users/login/
    Authentication: None required (AllowAny)

    REQUEST BODY (JSON):
    {
        "username": "john_doe",
        "password": "SecurePass123!"
    }

    SUCCESS RESPONSE (200 OK):
    {
        "message": "Login successful.",
        "user": {
            "id": 1,
            "username": "john_doe",
            "role": "rider",
            "rider_detail": { ... },  // only present for riders/rider_drivers
            "driver_detail": { ... }  // only present for drivers/rider_drivers
        },
        "tokens": {
            "access": "eyJ0eXAiOi...",
            "refresh": "eyJ0eXAiOi..."
        }
    }

    The frontend uses the 'role' field in the response to decide
    which dashboard/UI to show the user after login.

    ERROR RESPONSE (400 Bad Request):
    {
        "non_field_errors": ["Invalid username or password. Please try again."]
    }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle POST request to authenticate a user and return JWT tokens.

        STEP-BY-STEP FLOW:
        1. Pass credentials to the LoginSerializer
        2. Serializer validates credentials using Django's authenticate()
        3. If invalid credentials → return 400 error
        4. If valid → extract the user object
        5. Generate JWT tokens for the user
        6. Return 200 with full user profile (including role-specific nested data)
           so the frontend can immediately render the correct role-based UI

        Args:
            request: The HTTP request with username and password in the body.

        Returns:
            Response: 200 with user data + tokens, or 400 with error message.
        """
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # The validated data includes the 'user' key that was added in
        # the serializer's validate() method after successful authentication.
        user = serializer.validated_data['user']

        tokens = get_tokens_for_user(user)

        return Response(
            {
                'message': 'Login successful.',
                # UserProfileSerializer includes driver_detail and rider_detail
                # nested fields. The frontend checks user.role and user.driver_detail
                # or user.rider_detail to render the correct dashboard.
                'user': UserProfileSerializer(user).data,
                'tokens': tokens,
            },
            status=status.HTTP_200_OK
        )


class ProfileView(APIView):
    """
    API endpoint for viewing and updating the authenticated user's profile.

    URL: GET/PUT/PATCH /api/users/profile/
    Authentication: Required (JWT Bearer token)

    This endpoint always operates on the CURRENTLY LOGGED-IN user's profile.
    The user is identified from the JWT token in the Authorization header,
    NOT from a URL parameter. This prevents users from accessing or modifying
    other users' profiles.

    GET RESPONSE (200 OK):
    {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "role": "rider",
        "phone": "+919876543210",
        "rider_detail": { "rating": 4.5, "home_address": "..." },
        "driver_detail": null
    }

    PATCH REQUEST (partial update — only send changed fields):
    {
        "first_name": "Johnny",
        "phone": "+919999999999"
    }

    DIFFERENCE BETWEEN PUT AND PATCH:
    - PUT: requires ALL fields to be sent (full replacement)
    - PATCH: only send the fields you want to change (partial update)
    PATCH is more practical for profile updates because users usually
    only change one or two fields at a time.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return the authenticated user's profile data.

        request.user is automatically set by DRF's JWT authentication
        backend. When the client sends "Authorization: Bearer <token>",
        DRF decodes the token, finds the user_id claim, loads the user
        from the database, and sets request.user = that user object.

        Args:
            request: The HTTP request. request.user is the authenticated user.

        Returns:
            Response: 200 with the user's profile data serialized as JSON.
        """
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        """
        Fully update the authenticated user's profile.

        PUT semantics require ALL writable fields to be present in the
        request body. Missing fields will be set to their default/null.

        Args:
            request: The HTTP request with full profile data.

        Returns:
            Response: 200 with updated profile data, or 400 with errors.
        """
        # instance=request.user tells the serializer "update THIS user"
        # data=request.data provides the new field values
        # Together, this triggers the serializer's update() method instead of create().
        serializer = UserProfileSerializer(
            instance=request.user,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                'message': 'Profile updated successfully.',
                'user': serializer.data,
            },
            status=status.HTTP_200_OK
        )

    def patch(self, request):
        """
        Partially update the authenticated user's profile.

        PATCH is similar to PUT but with partial=True, which means the user
        only needs to send the fields they want to change. Fields not included
        in the request body will keep their current values.

        EXAMPLE:
        If the user only wants to update their phone number, they send:
        {"phone": "+919999999999"}
        And email, first_name, last_name, etc. remain unchanged.

        Args:
            request: The HTTP request with partial profile data.

        Returns:
            Response: 200 with updated profile data, or 400 with errors.
        """
        # partial=True is the key difference from PUT.
        # It tells the serializer: "don't require all fields,
        # only validate and update the fields that were provided".
        serializer = UserProfileSerializer(
            instance=request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                'message': 'Profile updated successfully.',
                'user': serializer.data,
            },
            status=status.HTTP_200_OK
        )


class DriverDetailUpdateView(APIView):
    """
    API endpoint for drivers to update their driver-specific information.

    URL: PATCH /api/users/driver-detail/
    Authentication: Required (JWT Bearer token)
    Permission: Only users with role='driver' or 'rider_driver' can access this.

    This endpoint lets a driver update their vehicle and license info.
    Fields like 'is_approved' and 'rating' are read-only and cannot be
    changed by the driver themselves.

    REQUEST BODY (JSON — send only fields you want to update):
    {
        "vehicle_number": "MH12AB1234",
        "vehicle_type": "car",
        "vehicle_model": "Toyota Innova",
        "is_online": true
    }

    SUCCESS RESPONSE (200 OK):
    {
        "message": "Driver details updated successfully.",
        "driver_detail": {
            "license_number": "...",
            "vehicle_type": "car",
            ...
        }
    }
    """

    # ---------------------------------------------------------------
    # IsRiderOrDriver: a custom permission that allows access to users
    # who have the 'driver' or 'rider_driver' role. Riders-only cannot
    # access this endpoint.
    # ---------------------------------------------------------------
    permission_classes = [IsAuthenticated, IsDriver]

    def patch(self, request):
        """
        Partially update the authenticated driver's DriverDetail record.

        get_or_create() is used as a safety net: it either fetches the
        existing DriverDetail, or creates a new empty one if it somehow
        doesn't exist. This prevents a 404 crash even if the detail record
        was somehow not created at registration.

        Args:
            request: The HTTP request with partial driver detail data.

        Returns:
            Response: 200 with updated driver_detail, or 400 with errors.
        """
        # get_or_create() returns a tuple: (instance, created_bool).
        # We only need the instance, so we use [0] to unpack it.
        driver_detail, _ = DriverDetail.objects.get_or_create(user=request.user)

        serializer = DriverDetailSerializer(
            instance=driver_detail,
            data=request.data,
            partial=True  # Only update the fields that were sent
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                'message': 'Driver details updated successfully.',
                'driver_detail': serializer.data,
            },
            status=status.HTTP_200_OK
        )


class RiderDetailUpdateView(APIView):
    """
    API endpoint for riders to update their rider-specific information.

    URL: PATCH /api/users/rider-detail/
    Authentication: Required (JWT Bearer token)
    Permission: Only users with role='rider' or 'rider_driver' can access this.

    REQUEST BODY (JSON — send only fields you want to update):
    {
        "home_address": "123 MG Road, Pune",
        "default_payment_method_id": "pm_abc123"
    }

    SUCCESS RESPONSE (200 OK):
    {
        "message": "Rider details updated successfully.",
        "rider_detail": {
            "rating": 4.8,
            "home_address": "123 MG Road, Pune",
            ...
        }
    }
    """

    permission_classes = [IsAuthenticated, IsRider]

    def patch(self, request):
        """
        Partially update the authenticated rider's RiderDetail record.

        Args:
            request: The HTTP request with partial rider detail data.

        Returns:
            Response: 200 with updated rider_detail, or 400 with errors.
        """
        rider_detail, _ = RiderDetail.objects.get_or_create(user=request.user)

        serializer = RiderDetailSerializer(
            instance=rider_detail,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                'message': 'Rider details updated successfully.',
                'rider_detail': serializer.data,
            },
            status=status.HTTP_200_OK
        )


class ChangePasswordView(APIView):
    """
    API endpoint for changing the authenticated user's password.

    URL: POST /api/users/change-password/
    Authentication: Required (JWT Bearer token)

    REQUEST BODY (JSON):
    {
        "old_password": "CurrentPass123!",
        "new_password": "NewSecurePass456!",
        "new_password_confirm": "NewSecurePass456!"
    }

    SUCCESS RESPONSE (200 OK):
    {
        "message": "Password changed successfully."
    }

    ERROR RESPONSE (400 Bad Request):
    {
        "old_password": ["Old password is incorrect."]
    }

    SECURITY NOTES:
    - Requires the old password to prevent unauthorized password changes
    - The new password goes through Django's password validators
    - After changing the password, EXISTING tokens remain valid
      (in production, you might want to invalidate all tokens)
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Handle POST request to change the user's password.

        STEP-BY-STEP FLOW:
        1. Pass the request data to ChangePasswordSerializer
        2. Serializer validates:
           a. Old password is correct (check_password against DB hash)
           b. New passwords match each other
           c. New password meets strength requirements
        3. If valid, use set_password() to hash and save the new password
        4. Return success message

        WHY set_password() + save()?
        user.set_password() does two things:
          1. Hashes the new password using PBKDF2 with a random salt
          2. Sets the hashed value on the user object (in memory)
        user.save() then writes the new hashed password to the database.

        We DON'T do user.password = new_password because that would store
        the raw password as plain text — a catastrophic security vulnerability.

        Args:
            request: The HTTP request with old and new passwords.

        Returns:
            Response: 200 on success, 400 on validation failure.
        """
        # context={'request': request} passes the request object to the
        # serializer so it can access request.user in validate_old_password().
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        # Get the currently authenticated user
        user = request.user

        # set_password() hashes the new password and sets it on the user object.
        # It does NOT save to the database — we need to call save() separately.
        user.set_password(serializer.validated_data['new_password'])

        # save() writes the new hashed password to the database.
        # update_fields=['password'] is an optimization: it tells Django
        # to only update the password column, not all columns.
        user.save(update_fields=['password'])

        return Response(
            {'message': 'Password changed successfully.'},
            status=status.HTTP_200_OK
        )
