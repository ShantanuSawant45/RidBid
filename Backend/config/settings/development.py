"""
Development settings for RideBid.
DEBUG=True, relaxed security, local services.
"""

from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ['*']

# Use console email backend in development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS — allow all in development (we'll add django-cors-headers later)
# CORS_ALLOW_ALL_ORIGINS = True
