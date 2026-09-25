"""
Serializers for the Users app.

WHAT ARE SERIALIZERS?
---------------------
Serializers are the bridge between Python objects (Django models) and JSON data
that gets sent over the internet to mobile apps or frontend clients.

They do TWO jobs:
  1. SERIALIZATION (Python → JSON): Take a CustomUser model instance and convert
     it into a JSON dictionary like {"username": "john", "role": "rider", ...}
     so it can be sent as an API response.

  2. DESERIALIZATION (JSON → Python): Take incoming JSON data from a request
     (like a registration form), validate it (is the email valid? is the password
     strong enough?), and create/update a model instance in the database.

Think of serializers as Django Forms, but for APIs instead of HTML pages.

WHY THIS FILE?
--------------
This file defines serializers for:
  - UserRegistrationSerializer: handles new user sign-up (creates account)
  - UserLoginSerializer: handles login (validates credentials, returns tokens)
  - UserProfileSerializer: handles viewing/updating user profile info
  - ChangePasswordSerializer: handles password change for logged-in users
"""

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration (sign-up).

    WHAT IT DOES:
    - Accepts: username, email, password, password_confirm, role, phone_number
    - Validates: passwords match, password is strong enough, email is unique
    - Creates: a new CustomUser in the database with a hashed password
    - Returns: the created user data (without password) + JWT tokens

    HOW IT WORKS:
    When a POST request comes in to /api/users/register/, DRF (Django REST Framework)
    passes the JSON body to this serializer. The serializer:
      1. Checks all field validations (required, max_length, etc.)
      2. Runs custom validation methods (validate_email, validate)
      3. If all validations pass, calls the create() method
      4. Returns the serialized user data
    """

    # ---------------------------------------------------------------
    # password: write_only=True means this field is accepted in input
    #   but NEVER included in the output/response. You don't want to
    #   send the password back in the API response!
    # validators=[validate_password]: uses Django's built-in password
    #   validators (minimum 8 chars, not too common, not all numeric, etc.)
    # ---------------------------------------------------------------
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password],
        help_text="Must be at least 8 characters, not entirely numeric, not too common."
    )

    # ---------------------------------------------------------------
    # password_confirm: a second password field to prevent typos.
    #   This is NOT stored in the database — it only exists for validation.
    #   write_only=True: same reason as password, never send it back.
    # ---------------------------------------------------------------
    password_confirm = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Must match the password field exactly."
    )

    class Meta:
        """
        Meta class tells the serializer which model to use and which fields
        to include. 'fields' lists every field this serializer handles.
        'read_only_fields' are fields that appear in the response but
        cannot be set by the user (Django manages them automatically).
        """
        model = CustomUser
        fields = [
            'id',                # Auto-generated primary key (read-only)
            'username',          # Required: unique login identifier
            'email',             # Required: user's email address
            'password',          # Required: will be hashed before storing
            'password_confirm',  # Required: must match password
            'role',              # Optional: defaults to 'rider'
            'phone_number',      # Optional: contact number
            'first_name',        # Optional: user's first name
            'last_name',         # Optional: user's last name
        ]
        read_only_fields = ['id']

    def validate_email(self, value):
        """
        Custom validation for the email field.

        This method is automatically called by DRF because it follows the
        naming convention: validate_<field_name>. DRF calls it during
        the validation phase with the email value.

        WHY: We need to ensure no two users share the same email address.
        Django's built-in User model doesn't enforce email uniqueness by
        default (only username is unique), so we check manually.

        Args:
            value (str): The email address submitted by the user.

        Returns:
            str: The validated (lowercased) email address.

        Raises:
            serializers.ValidationError: If a user with this email already exists.
        """
        # .lower() normalizes the email so "John@Email.com" and "john@email.com"
        # are treated as the same address.
        value = value.lower()

        # Check if any existing user already has this email address.
        # .exists() is efficient — it stops at the first match instead of
        # loading the entire user object from the database.
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email address already exists."
            )

        return value

    def validate(self, attrs):
        """
        Object-level validation — runs AFTER all individual field validations.

        This method receives ALL validated fields as a dictionary (attrs).
        It's used for validations that depend on multiple fields — in this
        case, checking that password and password_confirm match.

        Args:
            attrs (dict): Dictionary of all validated field values.
                Example: {'username': 'john', 'password': 'Secret123!', ...}

        Returns:
            dict: The validated attributes (with password_confirm removed).

        Raises:
            serializers.ValidationError: If passwords don't match.
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': "Passwords do not match."
            })

        # Remove password_confirm from the data because it's not a model field.
        # If we leave it in, Django will try to pass it to CustomUser.objects.create()
        # and raise an error because 'password_confirm' is not a database column.
        attrs.pop('password_confirm')

        return attrs

    def create(self, validated_data):
        """
        Create and return a new CustomUser instance.

        This method is called by the serializer's .save() method AFTER all
        validations have passed. It receives the clean, validated data.

        WHY create_user() INSTEAD OF create()?
        We use create_user() instead of CustomUser.objects.create() because
        create_user() automatically HASHES the password. If we used create(),
        the raw password would be stored in the database as plain text — a
        massive security vulnerability.

        create_user() flow:
          1. Takes the raw password ("Secret123!")
          2. Hashes it using PBKDF2 algorithm with a random salt
          3. Stores something like "pbkdf2_sha256$260000$salt$hash" in the DB
          4. Creates the user record with all other fields

        Args:
            validated_data (dict): Clean data after all validations.
                Example: {'username': 'john', 'password': 'Secret123!',
                         'email': 'john@example.com', 'role': 'rider'}

        Returns:
            CustomUser: The newly created user instance.
        """
        # Pop the password out of validated_data because create_user()
        # expects it as a separate argument, not inside **kwargs.
        password = validated_data.pop('password')

        # create_user() is a method provided by Django's UserManager.
        # It handles password hashing and normalizing the email.
        # **validated_data unpacks the remaining fields (username, email,
        # role, phone_number, etc.) as keyword arguments.
        user = CustomUser.objects.create_user(
            password=password,
            **validated_data
        )

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


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing and updating user profile.

    WHAT IT DOES:
    - READ: when a GET request comes in, this serializer converts the
      CustomUser model instance into JSON with all the fields listed below.
    - UPDATE: when a PATCH/PUT request comes in, this serializer validates
      the incoming data and updates the user's profile in the database.

    SECURITY:
    - 'id', 'username', 'role', 'date_joined' are read_only — users cannot
      change their username or role after registration (role changes could
      be a separate admin-only feature).
    - 'password' is NOT included — use the ChangePasswordSerializer instead.
    """

    class Meta:
        model = CustomUser
        fields = [
            'id',              # Primary key, auto-generated, read-only
            'username',        # Login identifier, read-only (can't change)
            'email',           # Can be updated
            'first_name',      # Can be updated
            'last_name',       # Can be updated
            'role',            # Read-only (rider/driver, set at registration)
            'phone_number',    # Can be updated
            'date_joined',     # Auto-set by Django, read-only
        ]
        # ---------------------------------------------------------------
        # read_only_fields: these fields appear in API responses but cannot
        # be modified by the user through this serializer. The API will
        # silently ignore any values provided for these fields in a
        # PATCH/PUT request.
        # ---------------------------------------------------------------
        read_only_fields = ['id', 'username', 'role', 'date_joined']

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
        if CustomUser.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError(
                "A user with this email address already exists."
            )

        return value


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
