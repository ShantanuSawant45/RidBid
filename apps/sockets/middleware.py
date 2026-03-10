"""
Custom JWT Authentication Middleware for Django Channels.

WHY DO WE NEED THIS?
--------------------
Django REST Framework (DRF) handles JWT authentication perfectly for HTTP requests
(like POST /api/bids/). It reads the "Authorization: Bearer <token>" header,
verifies it, and sets `request.user`.

However, WebSockets do NOT use DRF. They establish a persistent TCP connection
using Django Channels. Because of security restrictions in browsers (and standard
WebSocket implementations), you often CANNOT send custom headers like "Authorization"
during the initial WebSocket handshake.

Instead, mobile apps pass the token in the URL query string:
  ws://localhost:8000/ws/rides/5/?token=<jwt_token>

This middleware intercepts the WebSocket connection, extracts the token from the
query string, decodes it using SimpleJWT, finds the user in the database, and
attaches the user object to the WebSocket scope (`scope['user']`).
"""

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken

User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_string):
    """
    Decode the JWT token and retrieve the user from the database.

    Since database operations in Django are synchronous and Channels runs
    asynchronously (asyncio), we MUST wrap database calls in @database_sync_to_async.
    If we don't, Django will throw a SynchronousOnlyOperation error.

    Args:
        token_string (str): The raw JWT token string.

    Returns:
        CustomUser: The authenticated user, or AnonymousUser if invalid.
    """
    try:
        # UntypedToken verifies the token's signature and expiration using
        # our SECRET_KEY. It raises an exception if the token is invalid.
        decoded_data = UntypedToken(token_string)
    except (InvalidToken, TokenError):
        return AnonymousUser()

    # The token is valid. Extract the user_id payload.
    user_id = decoded_data.get('user_id')

    try:
        # Fetch the user from the database.
        user = User.objects.get(id=user_id)
        
        # Ensure the account is still active (e.g., hasn't been banned)
        if not user.is_active:
            return AnonymousUser()
            
        return user
    except User.DoesNotExist:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Middleware that intercepts WebSocket connections to authenticate users via JWT.
    """

    async def __call__(self, scope, receive, send):
        """
        This method is called when a new WebSocket connection is attempted.
        """
        # The query string is a bytes object, so we decode it to a string.
        # Example scope['query_string']: b'token=eyJhbG...'
        query_string = scope.get('query_string', b'').decode('utf-8')
        
        # parse_qs converts 'token=abc&foo=bar' into {'token': ['abc'], 'foo': ['bar']}
        query_params = parse_qs(query_string)

        # Extract the token if it exists
        token = query_params.get('token')

        if token:
            # token[0] gets the first value since parse_qs returns lists
            user = await get_user_from_token(token[0])
            # Attach the user to the scope (similar to request.user in HTTP)
            scope['user'] = user
        else:
            # No token provided
            scope['user'] = AnonymousUser()

        # Pass control to the next middleware or the consumer
        return await super().__call__(scope, receive, send)
