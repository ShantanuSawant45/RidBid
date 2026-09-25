"""
Root URL Configuration for RideBid project.

HOW DJANGO URL ROUTING WORKS:
------------------------------
When a request comes in (e.g., GET /api/users/profile/), Django processes
the URL through a chain of URL configurations:

  1. Django starts at ROOT_URLCONF (set in settings as 'config.urls')
  2. It tries to match the URL against each pattern in urlpatterns (top to bottom)
  3. If a pattern uses include(), Django strips the matched prefix and
     passes the REMAINING URL to the included URL config

EXAMPLE FLOW for GET /api/users/profile/:
  Step 1: config/urls.py sees 'api/users/' matches → strips 'api/users/'
  Step 2: apps/users/urls.py receives 'profile/' → matches ProfileView
  Step 3: ProfileView.get() handles the request

URL NAMESPACE:
Using namespace='users' in include() allows us to reference URLs by name:
  reverse('users:user-profile')  →  '/api/users/profile/'
This is useful for generating URLs in code without hardcoding paths.

CURRENT API ENDPOINTS:
  GET    /api/                             → Health check
  GET    /admin/                           → Django admin panel
  POST   /api/users/register/              → User registration
  POST   /api/users/login/                 → User login
  GET    /api/users/profile/               → View own profile
  PUT    /api/users/profile/               → Full profile update
  PATCH  /api/users/profile/               → Partial profile update
  POST   /api/users/change-password/       → Change password
  POST   /api/users/token/refresh/         → Refresh JWT token
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def api_root(request):
    """
    Health check endpoint.

    This is a simple endpoint that returns a JSON response confirming
    the API is running. It's useful for:
    - Monitoring tools that ping the API to check if it's alive
    - Load balancers that need a health check URL
    - Developers testing if the server is running

    No authentication required — it's a public endpoint.

    Args:
        request: The incoming HTTP request (not used, but required by Django).

    Returns:
        JsonResponse: A JSON object with status, message, and version.
    """
    return JsonResponse({
        'status': 'ok',
        'message': 'RideBid API is running',
        'version': '1.0.0',
    })


urlpatterns = [
    # ---------------------------------------------------------------
    # Django Admin Panel.
    # URL: /admin/
    # This provides a built-in web interface for managing database
    # records (users, rides, bids, etc.). Only users with is_staff=True
    # can access it. Access it by creating a superuser with:
    #   python manage.py createsuperuser
    # ---------------------------------------------------------------
    path('admin/', admin.site.urls),

    # ---------------------------------------------------------------
    # API Health Check.
    # URL: GET /api/
    # Returns: {"status": "ok", "message": "RideBid API is running"}
    # No auth required.
    # ---------------------------------------------------------------
    path('api/', api_root, name='api-root'),

    # ---------------------------------------------------------------
    # Users API — registration, login, profile, password change.
    # All URLs under /api/users/ are handled by apps/users/urls.py.
    # include() delegates URL matching to the users app's URL config.
    # namespace='users' allows reverse URL lookups like:
    #   reverse('users:user-login')  →  '/api/users/login/'
    # ---------------------------------------------------------------
    path('api/users/', include('apps.users.urls', namespace='users')),

    # ---------------------------------------------------------------
    # Rides API — create, list, search, update, cancel ride requests.
    # All URLs under /api/rides/ are handled by apps/rides/urls.py.
    # ---------------------------------------------------------------
    path('api/rides/', include('apps.rides.urls', namespace='rides')),

    # ---------------------------------------------------------------
    # Bids API — place, list, accept, and cancel bids.
    # All URLs under /api/bids/ are handled by apps/bids/urls.py.
    # ---------------------------------------------------------------
    path('api/bids/', include('apps.bids.urls', namespace='bids')),
]
