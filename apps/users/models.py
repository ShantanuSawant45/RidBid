"""
Custom User Model for RideBid.

WHY A CUSTOM USER MODEL?
-------------------------
Django comes with a built-in User model (username, email, password, etc.),
but RideBid needs two extra fields:
  1. 'role' — is this user a Rider (looking for rides) or a Driver (offering rides)?
  2. 'phone_number' — used for contact/verification.

Django's official recommendation is to ALWAYS create a custom user model at the
START of any project, because switching from the default User model to a custom
one after migrations have been run is extremely difficult. That's why we extend
AbstractUser — it gives us all the built-in fields (username, email, password,
first_name, last_name, is_active, is_staff, date_joined) PLUS our custom ones.

IMPORTANT: This model is referenced in settings via AUTH_USER_MODEL = 'users.CustomUser'.
Every time Django needs to look up "who is the User?", it uses this model instead
of the default django.contrib.auth.models.User.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Custom user model that extends Django's built-in AbstractUser.

    Inherits all standard fields from AbstractUser:
    - username: unique identifier for login
    - email: email address
    - password: hashed password (Django handles hashing automatically)
    - first_name, last_name: user's real name
    - is_active: whether the account is active (can login)
    - is_staff: whether user can access Django admin
    - is_superuser: whether user has all permissions
    - date_joined: when the account was created
    - last_login: when the user last logged in

    Custom fields added for RideBid:
    - role: either 'rider' or 'driver' — determines what features the user sees
    - phone_number: optional phone number for contact/SMS verification
    """

    # ---------------------------------------------------------------
    # Role choices using Django's TextChoices enum.
    # TextChoices creates a clean enumeration where:
    #   - 'rider' is stored in the database
    #   - 'Rider' is the human-readable label shown in forms/admin
    # Using an enum prevents typos (you write Role.RIDER, not 'rider')
    # and makes code more readable and maintainable.
    # ---------------------------------------------------------------
    class Role(models.TextChoices):
        RIDER = 'rider', 'Rider'      # Users who request rides
        DRIVER = 'driver', 'Driver'    # Users who offer rides and bid on requests

    # ---------------------------------------------------------------
    # 'role' field — CharField with constrained choices.
    # max_length=10: both 'rider' (5 chars) and 'driver' (6 chars) fit.
    # choices=Role.choices: Django enforces that only 'rider' or 'driver'
    #   can be stored. Also auto-generates a dropdown in admin/forms.
    # default=Role.RIDER: new users are Riders by default. They can
    #   switch to Driver during registration or later.
    # ---------------------------------------------------------------
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.RIDER,
    )

    # ---------------------------------------------------------------
    # 'phone_number' field — optional contact number.
    # max_length=15: international phone numbers can be up to 15 digits
    #   (E.164 standard), e.g., +919876543210.
    # blank=True: the field is optional in forms (user can leave it empty).
    # null=True: the database stores NULL if no phone number is provided.
    # ---------------------------------------------------------------
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        # ---------------------------------------------------------------
        # db_table: explicitly sets the database table name to 'users'
        #   instead of the auto-generated 'users_customuser'.
        # verbose_name / verbose_name_plural: controls how this model
        #   appears in the Django admin interface.
        # ---------------------------------------------------------------
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        """
        String representation of the user.
        Called when you print(user) or display the user in admin.
        Returns something like: "john_doe (rider)" or "jane (driver)".
        """
        return f"{self.username} ({self.role})"

    @property
    def is_rider(self):
        """
        Convenience property to check if this user is a Rider.
        Usage: if user.is_rider: ...
        Returns True if the user's role is 'rider', False otherwise.

        This is a @property, which means you call it like an attribute
        (user.is_rider) not like a method (user.is_rider()).
        """
        return self.role == self.Role.RIDER

    @property
    def is_driver(self):
        """
        Convenience property to check if this user is a Driver.
        Usage: if user.is_driver: ...
        Returns True if the user's role is 'driver', False otherwise.
        """
        return self.role == self.Role.DRIVER
