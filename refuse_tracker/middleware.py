# refuse_tracker/middleware.py

from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

@database_sync_to_async
def get_user(validated_token):
    """
    Fetch user from token. Import models here to avoid AppRegistryNotReady.
    """
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import AnonymousUser

    User = get_user_model()
    try:
        user_id = validated_token['user_id']
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom JWT auth middleware for Django Channels.
    Reads 'token' from WebSocket query string and attaches user to scope.
    """
    async def __call__(self, scope, receive, send):
        # Import here to avoid AppRegistryNotReady
        from rest_framework_simplejwt.tokens import UntypedToken
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
        from django.contrib.auth.models import AnonymousUser

        # Parse token from query string
        query_string = parse_qs(scope.get("query_string", b"").decode())
        token_list = query_string.get("token")

        if token_list:
            token = token_list[0]
            try:
                validated_token = UntypedToken(token)
                scope["user"] = await get_user(validated_token)
            except (InvalidToken, TokenError):
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)
