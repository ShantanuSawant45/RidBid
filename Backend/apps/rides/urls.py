"""
URL routing for the Rides app.

HOW THESE URLS CONNECT TO THE REST OF THE PROJECT:
---------------------------------------------------
These URL patterns are mounted at 'api/rides/' by config/urls.py.
So the full URLs become:

  POST   /api/rides/                    → RideCreateView (create a ride)
  GET    /api/rides/my-rides/           → MyRidesView (rider's own rides)
  GET    /api/rides/available/          → AvailableRidesView (biddable rides)
  GET    /api/rides/nearby/             → NearbyRidesView (geospatial search)
  GET    /api/rides/<id>/               → RideDetailView (single ride detail)
  PATCH  /api/rides/<id>/update/        → RideUpdateView (edit a ride)
  POST   /api/rides/<id>/cancel/        → RideCancelView (cancel a ride)

URL DESIGN RATIONALE:
- List/Create are at the root (/api/rides/)
- Action endpoints use verbs (/cancel/, /update/) for clarity
- Detail views use the ride ID as a path parameter (<int:ride_id>/)
- <int:ride_id> tells Django to match only integer values and pass
  them to the view as a keyword argument named 'ride_id'
"""

from django.urls import path

from .views import (
    RideCreateView,
    MyRidesView,
    AvailableRidesView,
    NearbyRidesView,
    RideDetailView,
    RideUpdateView,
    RideCancelView,
)

app_name = 'rides'
urlpatterns = [
    path('',RideCreateView.as_view(),name='ride-create'),
    path('my-rides/',MyRidesView.as_view(),name='my-rides'),
    path('available/',AvailableRidesView.as_view(),name='available-rides'),
    path('nearby/',NearbyRidesView.as_view(),name='nearby-rides'),
    path('<int:ride_id>/',RideDetailView.as_view(),name='ride-detail'),
    path('<int:ride_id>/update/',RideUpdateView.as_view(),name='ride-update'),
    path('<int:ride_id>/cancel/',RideCancelView.as_view(),name='ride-cancel'),
]
