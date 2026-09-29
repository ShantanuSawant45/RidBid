from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, DriverDetail, RiderDetail, Role


class DriverDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for the DriverDetail model.

    WHAT IT DOES:
    - READ  : converts a DriverDetail instance into JSON so the API can
              return a driver's license info, vehicle info, rating, etc.
    - WRITE : validates and saves incoming driver detail data (e.g., when
              a driver updates their vehicle information).

    This is a NESTED serializer — it will be embedded inside UserProfileSerializer
    so that a driver's full profile looks like:
    {
        "id": 1,
        "username": "...",
        ...user fields...
        "driver_detail": {          ← this is what DriverDetailSerializer produces
            "license_number": "...",
            "vehicle_type": "car",
            ...
        }
    }
    """
    class Meta:
        # Tell the serializer which model and which fields to use.
        model = DriverDetail
        fields = [
            'license_number',   # Driver's license ID
            'license_expiry',   # Expiry date for the license
            'vehicle_number',   # License plate (e.g., "MH12AB1234")
            'vehicle_type',     # car / bike / suv / van / truck
            'vehicle_model',    # e.g., "Toyota Innova"
            'is_approved',      # Set by admin, read-only for drivers
            'rating',           # Driver's average rating
            'is_online',        # Whether the driver is currently available
        ]
        # ---------------------------------------------------------------
        # read_only_fields: these appear in responses but cannot be
        # changed by the driver through this serializer. 'is_approved'
        # should only be set by admins, not by the driver themselves.
        # 'rating' is calculated from completed rides, not user-submitted.
        # ---------------------------------------------------------------
        read_only_fields = ['is_approved', 'rating']


class RiderDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for the RiderDetail model.

    WHAT IT DOES:
    Similar to DriverDetailSerializer but for rider-specific data.
    A rider's profile extension stores their rating and home address.
    """
    class Meta:
        model = RiderDetail
        fields = [
            'rating',                   # Rider's average rating (read-only)
            'default_payment_method_id', # Stored payment method reference
            'home_address',             # Rider's saved home address
        ]
        read_only_fields = ['rating']



class UserRegistrationSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password],
        help_text="Must be at least 8 characters, not entirely numeric, not too common."
    )
    password_confirm = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Must match the password field exactly."
    )

    class Meta:
        model = User
        fields = [
            'id',               # Auto-generated primary key (read-only)
            'username',         # Required: unique login identifier
            'email',            # Required: user's email address
            'password',         # Required: will be hashed before storing
            'password_confirm', # Required: must match password (not saved to DB)
            'role',             # Optional: 'rider' | 'driver' | 'rider_driver'
            'phone',            # Optional: contact number (unique)
            'first_name',       # Optional: user's first name
            'last_name',        # Optional: user's last name
        ]
        read_only_fields = ['id']

    def validate_email(self, value):
        # this method is called automatically by drf 
        value = value.lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email address already exists."
            )

        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': "Passwords do not match."
            })
        attrs.pop('password_confirm')
        return attrs

    def create(self, validated_data):
        from django.db import transaction
        password = validated_data.pop('password')
        role = validated_data.get('role', Role.RIDER)
        with transaction.atomic():
            user = User.objects.create_user(
                password=password,
                **validated_data
            )

            if role in (Role.DRIVER, Role.RIDER_DRIVER):
                DriverDetail.objects.create(user=user)
            if role in (Role.RIDER, Role.RIDER_DRIVER):
                RiderDetail.objects.create(user=user)

        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login (authentication).

    WHAT IT DOES:
    - Accepts: username and password
    - Validates: credentials are correct, account is active
    - Returns: JWT access token + refresh token + user info

    THIS IS NOT A ModelSerializer — it's a plain Serializer because we're not
    creating/updating a model. We're just validating credentials and generating tokens.

    JWT TOKEN FLOW:
    1. User sends username + password to /api/users/login/
    2. This serializer validates the credentials
    3. If valid, we generate two JWT tokens:
       - Access Token: short-lived (30 min), used to authenticate API requests
       - Refresh Token: long-lived (7 days), used to get a new access token
    4. The client (mobile app) stores both tokens and sends the access token
       in the Authorization header: "Bearer <access_token>"
    5. When the access token expires, the client uses the refresh token to
       get a new access token without asking the user to log in again
    """

    # ---------------------------------------------------------------
    # Input fields (what the user sends in the request body).
    # These are NOT model fields — they're just data we need to validate.
    # ---------------------------------------------------------------
    username = serializers.CharField(
        help_text="The user's username."
    )
    password = serializers.CharField(
        write_only=True,
        help_text="The user's password. Never returned in responses."
    )

    def validate(self, attrs):
        """
        Validate the login credentials.

        This method uses Django's built-in authenticate() function which:
          1. Looks up the user by username
          2. Hashes the provided password with the same salt
          3. Compares the hash with the stored hash
          4. Returns the user if they match, None if they don't

        This is secure because we NEVER compare raw passwords — only hashes.

        Args:
            attrs (dict): {'username': '...', 'password': '...'}

        Returns:
            dict: Validated data with the authenticated user object added.

        Raises:
            serializers.ValidationError: If credentials are invalid or
                the account is deactivated.
        """
        username = attrs.get('username')
        password = attrs.get('password')

        # authenticate() is Django's built-in function that checks credentials.
        # It returns the User object if credentials are valid, None otherwise.
        # Under the hood, it hashes the password and compares with the DB hash.
        user = authenticate(username=username, password=password)

        if user is None:
            raise serializers.ValidationError(
                "Invalid username or password. Please try again."
            )

        # Check if the user's account is active. Admins can deactivate users
        # by setting is_active=False in the admin panel. Deactivated users
        # should not be able to log in.
        if not user.is_active:
            raise serializers.ValidationError(
                "This account has been deactivated. Please contact support."
            )

        # Store the user object in the validated data so the view can access
        # it later to generate tokens and build the response.
        attrs['user'] = user
        return attrs


# ===========================================================================
# PROFILE SERIALIZER
# ===========================================================================

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing and updating user profile.

    WHAT IT DOES:
    - READ: when a GET request comes in, this serializer converts the
      User model instance into JSON. It also NESTS the appropriate
      detail serializer (DriverDetailSerializer or RiderDetailSerializer)
      so the full profile comes back in one response.
    - UPDATE: when a PATCH/PUT request comes in, this serializer validates
      the incoming data and updates the user's profile in the database.

    NESTED SERIALIZERS (read-only):
    The 'driver_detail' and 'rider_detail' fields use the SerializerMethodField
    approach — they are computed dynamically based on the user's role, so that:
      - A rider's profile shows 'rider_detail' (not 'driver_detail')
      - A driver's profile shows 'driver_detail' (not 'rider_detail')
      - A rider_driver shows BOTH

    SECURITY:
    - 'id', 'username', 'role', 'date_joined' are read_only — users cannot
      change their username or role through this endpoint.
    - 'password' is NOT included — use the ChangePasswordSerializer instead.
    """

    # ---------------------------------------------------------------
    # SerializerMethodField: calls the method get_<field_name>() on this
    # class. It's read-only by definition — perfect for computed/nested data.
    # ---------------------------------------------------------------
    driver_detail = serializers.SerializerMethodField()
    rider_detail = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',               # Primary key, auto-generated, read-only
            'username',         # Login identifier, read-only (can't change)
            'email',            # Can be updated
            'first_name',       # Can be updated
            'last_name',        # Can be updated
            'role',             # Read-only (rider/driver, set at registration)
            'phone',            # Can be updated
            'profile_picture_url', # Can be updated (URL to hosted image)
            'is_verified',      # Set by admin verification flow, read-only
            'date_joined',      # Auto-set by Django, read-only
            'driver_detail',    # Nested DriverDetail data (read-only, computed)
            'rider_detail',     # Nested RiderDetail data (read-only, computed)
        ]
        # ---------------------------------------------------------------
        # read_only_fields: these fields appear in API responses but cannot
        # be modified by the user through this serializer. The API will
        # silently ignore any values provided for these fields in a
        # PATCH/PUT request.
        # ---------------------------------------------------------------
        read_only_fields = [
            'id', 'username', 'role', 'date_joined',
            'is_verified', 'driver_detail', 'rider_detail'
        ]

    def get_driver_detail(self, obj):
        """
        Return serialized DriverDetail for this user, or None if they
        are not a driver.

        'obj' here is the User instance being serialized.
        hasattr() safely checks whether the related object exists — if the
        user has no DriverDetail row, accessing obj.driver_detail would raise
        a RelatedObjectDoesNotExist exception. hasattr() catches that and
        returns False instead of crashing.

        Args:
            obj (User): The user being serialized.

        Returns:
            dict | None: Serialized DriverDetail data, or None.
        """
        if hasattr(obj, 'driver_detail'):
            return DriverDetailSerializer(obj.driver_detail).data
        return None

    def get_rider_detail(self, obj):
        """
        Return serialized RiderDetail for this user, or None if they
        are not a rider.

        Same logic as get_driver_detail above, but for the RiderDetail
        related object.

        Args:
            obj (User): The user being serialized.

        Returns:
            dict | None: Serialized RiderDetail data, or None.
        """
        if hasattr(obj, 'rider_detail'):
            return RiderDetailSerializer(obj.rider_detail).data
        return None

    def validate_email(self, value):
        """
        Validate email uniqueness on profile update.

        Similar to the registration serializer, but with one difference:
        we EXCLUDE the current user from the uniqueness check. Why?
        If user "john" has email "john@email.com" and sends an update
        with the same email, we should NOT raise an error — they're
        keeping their own email, not stealing someone else's.

        self.instance is the current user being updated (set by DRF
        when the serializer is initialized with an existing object).

        Args:
            value (str): The email address submitted for update.

        Returns:
            str: The validated (lowercased) email.

        Raises:
            serializers.ValidationError: If another user already has this email.
        """
        value = value.lower()

        # .exclude(pk=self.instance.pk) removes the current user from
        # the query, so we only check if OTHER users have this email.
        if User.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError(
                "A user with this email address already exists."
            )

        return value


# ===========================================================================
# CHANGE PASSWORD SERIALIZER
# ===========================================================================

class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing a user's password.

    WHAT IT DOES:
    - Accepts: old_password, new_password, new_password_confirm
    - Validates: old password is correct, new passwords match,
      new password meets strength requirements
    - Updates: the user's password in the database (hashed)

    WHY A SEPARATE SERIALIZER?
    Password changes require the old password for verification (security).
    This is different from profile updates which don't need the old password.
    Keeping it separate also follows the Single Responsibility Principle.
    """

    # ---------------------------------------------------------------
    # old_password: the user's current password for verification.
    # We need this to prevent someone with a stolen session from
    # changing the password without knowing the original.
    # ---------------------------------------------------------------
    old_password = serializers.CharField(
        write_only=True,
        help_text="Your current password for verification."
    )

    # ---------------------------------------------------------------
    # new_password: the desired new password.
    # validators=[validate_password] runs Django's password validators:
    #   - MinimumLengthValidator: at least 8 characters
    #   - CommonPasswordValidator: not in list of 20,000 common passwords
    #   - NumericPasswordValidator: not entirely numeric
    #   - UserAttributeSimilarityValidator: not too similar to username/email
    # ---------------------------------------------------------------
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password],
        help_text="New password. Must be at least 8 characters."
    )

    new_password_confirm = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Repeat the new password to confirm."
    )

    def validate_old_password(self, value):
        """
        Verify that the old password is correct.

        self.context['request'].user gives us the currently authenticated user
        (the user making this API request). DRF automatically passes the
        request object in the serializer's context.

        user.check_password() hashes the provided value and compares it with
        the stored hash. It NEVER compares raw passwords directly.

        Args:
            value (str): The old password provided by the user.

        Returns:
            str: The validated old password.

        Raises:
            serializers.ValidationError: If the old password is incorrect.
        """
        user = self.context['request'].user

        if not user.check_password(value):
            raise serializers.ValidationError(
                "Old password is incorrect."
            )

        return value

    def validate(self, attrs):
        """
        Cross-field validation: ensure new passwords match.

        Args:
            attrs (dict): {'old_password': '...', 'new_password': '...',
                          'new_password_confirm': '...'}

        Returns:
            dict: Validated attributes.

        Raises:
            serializers.ValidationError: If new passwords don't match.
        """
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': "New passwords do not match."
            })

        return attrs
