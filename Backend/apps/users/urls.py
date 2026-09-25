"""
URL routing for the Users app.

WHAT IS URL ROUTING?
--------------------
URL routing maps URL patterns to view functions/classes. When a request
comes in, Django goes through the urlpatterns list TOP TO BOTTOM and tries
to match the request URL. When it finds a match, it calls the corresponding
view and stops looking.

HOW URL PATTERNS WORK:
  path('register/', RegisterView.as_view(), name='user-register')
    │                │                        │
    │                │                        └─ Name: a unique identifier
    │                │                           for this URL. Used in reverse()
    │                │                           to generate URLs programmatically.
    │                │
    │                └─ View: the class that handles requests to this URL.
    │                   .as_view() converts a class-based view into a
    │                   callable function that Django can use.
    │
    └─ Pattern: the URL path to match. This is RELATIVE to the parent
       URL config. Since config/urls.py mounts this at 'api/users/',
       the full URL becomes: /api/users/register/

FULL URL MAP (after including in config/urls.py):
  POST   /api/users/register/              → RegisterView
  POST   /api/users/login/                 → LoginView
  GET    /api/users/profile/               → ProfileView (get)
  PUT    /api/users/profile/               → ProfileView (put)
  PATCH  /api/users/profile/               → ProfileView (patch)
  POST   /api/users/change-password/       → ChangePasswordView
  POST   /api/users/token/refresh/         → TokenRefreshView (SimpleJWT built-in)

JWT TOKEN REFRESH ENDPOINT:
SimpleJWT provides a built-in TokenRefreshView that accepts a refresh token
and returns a new access token. This is critical for the mobile app because:
  1. User logs in → gets access token (30 min) + refresh token (7 days)
  2. After 30 min, access token expires
  3. App sends refresh token to /api/users/token/refresh/
  4. Gets back a new access token → user stays logged in
  5. After 7 days, refresh token expires → user must log in again
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    LoginView,
    ProfileView,
    ChangePasswordView,
)

# ---------------------------------------------------------------
# app_name: this is a namespace for URL names. It allows us to
# reference URLs as 'users:user-register' instead of just
# 'user-register'. This prevents name collisions when multiple
# apps have URLs with similar names (e.g., both users and rides
# might have a 'list' URL).
# ---------------------------------------------------------------
app_name = 'users'

urlpatterns = [
    # ---------------------------------------------------------------
    # Registration endpoint.
    # Method: POST
    # Auth: None (AllowAny — you can't have a token before registering)
    # Body: {username, email, password, password_confirm, role, phone_number}
    # Returns: user data + JWT tokens (user is auto-logged-in)
    # ---------------------------------------------------------------
    path(
        'register/',
        RegisterView.as_view(),
        name='user-register'
    ),

    # ---------------------------------------------------------------
    # Login endpoint.
    # Method: POST
    # Auth: None (AllowAny)
    # Body: {username, password}
    # Returns: user data + JWT tokens
    # ---------------------------------------------------------------
    path(
        'login/',
        LoginView.as_view(),
        name='user-login'
    ),

    # ---------------------------------------------------------------
    # Profile endpoint (view and edit own profile).
    # Methods: GET (view), PUT (full update), PATCH (partial update)
    # Auth: Required (JWT Bearer token)
    # GET returns: user profile data
    # PUT/PATCH body: {email, first_name, last_name, phone_number}
    # ---------------------------------------------------------------
    path(
        'profile/',
        ProfileView.as_view(),
        name='user-profile'
    ),

    # ---------------------------------------------------------------
    # Change password endpoint.
    # Method: POST
    # Auth: Required (JWT Bearer token)
    # Body: {old_password, new_password, new_password_confirm}
    # Returns: success message
    # ---------------------------------------------------------------
    path(
        'change-password/',
        ChangePasswordView.as_view(),
        name='user-change-password'
    ),

    # ---------------------------------------------------------------
    # Token refresh endpoint (provided by SimpleJWT).
    # Method: POST
    # Auth: None (the refresh token itself IS the auth)
    # Body: {"refresh": "eyJ0eXAiOiJKV1Q..."}
    # Returns: {"access": "eyJ0eXAiOiJKV1Q..."}
    #
    # This is a BUILT-IN view from the djangorestframework-simplejwt
    # package. We don't need to write any code — it handles:
    #   1. Validating the refresh token
    #   2. Checking it hasn't expired
    #   3. Generating a new access token
    #   4. Optionally rotating the refresh token (per our settings)
    # ---------------------------------------------------------------
    path(
        'token/refresh/',
        TokenRefreshView.as_view(),
        name='token-refresh'
    ),
]
