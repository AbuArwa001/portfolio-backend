import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
import requests

User = get_user_model()

class ClerkAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
            
        try:
            token = auth_header.split(' ')[1]
            
            # Verify the token using Clerk's API
            response = requests.get(
                f'https://api.clerk.dev/v1/sessions/{token}/verify',
                headers={
                    'Authorization': f'Bearer {settings.CLERK_SECRET_KEY}',
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code != 200:
                raise AuthenticationFailed('Invalid token')
                
            payload = response.json()
            
            # Get or create user
            user, created = User.objects.get_or_create(
                clerk_id=payload['user_id'],
                defaults={
                    'username': payload['user_id'],
                    'email': payload.get('email', ''),
                    'first_name': payload.get('first_name', ''),
                    'last_name': payload.get('last_name', ''),
                }
            )
            
            return (user, None)
            
        except (IndexError, KeyError, requests.RequestException) as e:
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')