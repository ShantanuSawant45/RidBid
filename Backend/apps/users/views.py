"""
API Views for the Users app.

WHAT ARE VIEWS?
---------------
Views are Python functions or classes that receive HTTP requests and return
HTTP responses. They are the "controller" in the MVC pattern — they sit
between the URL routing and the serializers/models, orchestrating the
request-response cycle.

DJANGO REST FRAMEWORK VIEWS:
DRF provides several view classes with increasing levels of abstraction:

  1. APIView (we use this for login/register):
     - Low-level: you manually handle GET, POST, PUT, DELETE methods.
     - Full control over the logic inside each method.
     - Best for custom logic that doesn't map to simple CRUD operations.

  2. GenericAPIView + Mixins:
     - Mid-level: provides common patterns like list, create, retrieve, update.
     - You compose behavior by mixing in classes.

  3. ViewSet (not used here yet):
     - High-level: combines list + create + retrieve + update + delete into
       one class with automatic URL routing.

REQUEST FLOW:
  1. Client sends HTTP request → Django matches URL pattern
  2. URL pattern routes to a view class/function
  3. DRF runs authentication (JWT token check)
  4. DRF runs permission checks (IsAuthenticated, IsRider, etc.)
  5. DRF calls the appropriate method (get, post, put, patch, delete)
  6. The view method processes the request and returns a Response

VIEWS IN THIS FILE:
  - RegisterView: POST /api/users/register/ — create new account
  - LoginView: POST /api/users/login/ — authenticate and get tokens
  - ProfileView: GET/PUT/PATCH /api/users/profile/ — view/edit own profile
  - ChangePasswordView: POST /api/users/change-password/ — change password
"""

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
)


def get_tokens_for_user(user):
    """
    Generate JWT access and refresh tokens for a given user.

    HOW JWT TOKENS WORK:
    JWT (JSON Web Token) is a compact, URL-safe token format. Each token
    contains encoded JSON data (called "claims") that includes:
      - user_id: which user this token belongs to
      - exp: when the token expires
      - iat: when the token was issued
      - jti: unique token identifier

    The token is digitally signed with our SECRET_KEY, so the server can
    verify it hasn't been tampered with. The client cannot modify the
    token without invalidating the signature.

    TWO TYPES OF TOKENS:
    1. Access Token (short-lived, 30 minutes):
       - Sent with every API request in the Authorization header
       - Example: "Authorization: Bearer eyJ0eXAiOiJKV1Q..."
       - If stolen, the damage is limited because it expires quickly

    2. Refresh Token (long-lived, 7 days):
       - Used ONLY to get a new access token
       - Sent to /api/users/token/refresh/ when the access token expires
       - Should be stored securely by the client

    WHY TWO TOKENS?
    If we only had one long-lived token, a stolen token would give an
    attacker access for a long time. With two tokens:
    - The frequently-used access token expires quickly (30 min)
    - The refresh token is used rarely and can be rotated/blacklisted

    Args:
        user (CustomUser): The user to generate tokens for.

    Returns:
        dict: A dictionary with 'refresh' and 'access' token strings.
            Example: {
                'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGci...',
                'access': 'eyJ0eXAiOiJKV1QiLCJhbGci...'
            }
    """
    # RefreshToken.for_user() creates a refresh token with the user's ID
    # encoded in it. The access token is derived from the refresh token.
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterView(APIView):
    """
    API endpoint for user registration (sign-up).

    URL: POST /api/users/register/
    Authentication: None required (AllowAny)
    Rate limiting: Should be added in production to prevent abuse

    REQUEST BODY (JSON):
    {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
        "role": "rider",         // optional, defaults to "rider"
        "phone_number": "+919876543210",  // optional
        "first_name": "John",    // optional
        "last_name": "Doe"       // optional
    }

    SUCCESS RESPONSE (201 Created):
    {
        "message": "Registration successful.",
        "user": {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com",
            "role": "rider",
            ...
        },
        "tokens": {
            "access": "eyJ0eXAiOi...",
            "refresh": "eyJ0eXAiOi..."
        }
    }

    ERROR RESPONSE (400 Bad Request):
    {
        "email": ["A user with this email address already exists."],
        "password": ["This password is too common."]
    }
    """

    # ---------------------------------------------------------------
    # permission_classes: controls who can access this endpoint.
    # AllowAny means no authentication is required — anyone can
    # register, even without a JWT token. This makes sense because
    # you can't have a token before you have an account!
    # ---------------------------------------------------------------
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle POST request to create a new user account.

        STEP-BY-STEP FLOW:
        1. DRF receives the POST request with JSON body
        2. We pass request.data to the serializer for validation
        3. serializer.is_valid() runs all validations:
           - Field-level: required fields present, types correct
           - Custom: email uniqueness, password strength, passwords match
        4. If invalid, return 400 with error details
        5. If valid, serializer.save() calls create() which:
           - Hashes the password
           - Creates the user in the database
        6. Generate JWT tokens for the new user
        7. Return 201 with user data + tokens

        Args:
            request: The HTTP request object. request.data contains
                the parsed JSON body (DRF handles JSON parsing
                automatically based on the Content-Type header).

        Returns:
            Response: DRF Response object with:
                - 201 status + user data + tokens on success
                - 400 status + error details on validation failure
        """
        # Pass the incoming JSON data to the serializer for validation.
        # data=request.data tells the serializer "validate and deserialize this".
        serializer = UserRegistrationSerializer(data=request.data)

        # is_valid() runs ALL validations:
        # 1. Required field checks
        # 2. Field type checks (CharField, EmailField, etc.)
        # 3. Custom validators (validate_email, validate, etc.)
        # raise_exception=True makes DRF automatically return a 400 response
        # with error details if validation fails, so we don't need an else branch.
        serializer.is_valid(raise_exception=True)

        # .save() calls the serializer's create() method because this is a
        # new object (no existing instance was passed to the serializer).
        # It returns the newly created CustomUser instance.
        user = serializer.save()

        # Generate JWT tokens so the user is immediately logged in
        # after registration (no need for a separate login request).
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
            "email": "john@example.com",
            "role": "rider",
            ...
        },
        "tokens": {
            "access": "eyJ0eXAiOi...",
            "refresh": "eyJ0eXAiOi..."
        }
    }

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
        6. Return 200 with user data + tokens

        The client (mobile app / frontend) should store the tokens:
        - Access token: sent in the Authorization header for subsequent requests
        - Refresh token: stored securely, used to get new access tokens

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
        "first_name": "John",
        "last_name": "Doe",
        "role": "rider",
        "phone_number": "+919876543210",
        "date_joined": "2026-04-23T00:00:00Z"
    }

    PATCH REQUEST (partial update):
    {
        "first_name": "Johnny",
        "phone_number": "+919999999999"
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
        {"phone_number": "+919999999999"}
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
