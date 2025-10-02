import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
import copy

from .models import BlacklistedToken

User = get_user_model()

class JWTAuthentication(BaseAuthentication):

    @staticmethod
    def generate_token(payload):
        expiration = datetime.utcnow() + timedelta(days=30)
        token_payload = copy.deepcopy(payload)
        token_payload['exp'] = int(expiration.timestamp())
        token_payload['type'] = 'access_token'
        token_payload['id'] = str(payload['id'])

        return jwt.encode(token_payload, key=settings.SECRET_KEY, algorithm='HS256')

    @staticmethod
    def generate_refresh_token(payload):
        expiration = datetime.utcnow() + timedelta(days=60)
        token_payload = copy.deepcopy(payload)
        token_payload['exp'] = int(expiration.timestamp())
        token_payload['type'] = 'refresh_token'
        token_payload['id'] = str(payload['id'])

        return jwt.encode(token_payload, key=settings.SECRET_KEY, algorithm='HS256')

    def extract_token(self, request):
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]
        return None

    def verify_token(self, payload, token_type='access_token'):
        if 'exp' not in payload:
            raise InvalidTokenError("Token has no expiration")

        exp_timestamp = payload['exp']
        current_timestamp = int(datetime.utcnow().timestamp())

        if current_timestamp > exp_timestamp:
            raise ExpiredSignatureError("Token has expired")

        if payload.get('type') != token_type:
            raise InvalidTokenError(f"Expected token type '{token_type}', got '{payload.get('type')}'")

    def authenticate(self, request):
        token = self.extract_token(request)
        if not token:
            return None

        try:
            # Decode the token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])

            # Verify the token
            self.verify_token(payload, token_type='access_token')

            if BlacklistedToken.objects.filter(token=token).exists():
                raise AuthenticationFailed("Token has been blacklisted.")

            # Extract user ID from payload
            user_id = payload.get('id')
            if not user_id:
                raise AuthenticationFailed("Token missing user ID.")

            # Look up user by ID
            user = User.objects.get(id=user_id)

            return (user, token)

        except (InvalidTokenError, ExpiredSignatureError, User.DoesNotExist, jwt.DecodeError) as e:
            # If there's an error, log it
            raise AuthenticationFailed(f"Invalid Token: {str(e)}")