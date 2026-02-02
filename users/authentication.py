import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from jwt import PyJWKClient
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()

class ClerkAuthenticationBackend(BaseBackend):
    def __init__(self):
        self.jwks_client = PyJWKClient(settings.CLERK_JWKS_URL)
    
    def authenticate(self, request, token=None):
        if not token:
            return None
            
        try:
            # Verify the JWT token
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            data = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.CLERK_PUBLISHABLE_KEY,
                options={"verify_exp": True},
            )
            
            # Extract user data from the token
            clerk_user_id = data.get("sub")
            email = data.get("email")
            
            if not clerk_user_id:
                return None
                
            # Get or create the user
            user, created = User.objects.get_or_create(
                clerk_user_id=clerk_user_id,
                defaults={
                    "username": email or clerk_user_id,
                    "email": email,
                }
            )
            
            # Update user data if needed
            if not created:
                if email and user.email != email:
                    user.email = email
                    user.save()
            
            return user
            
        except jwt.InvalidTokenError:
            return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

class ClerkTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header:
            return None
            
        try:
            # Extract the token from the header
            token = auth_header.split(' ')[1]  # Bearer <token>
            
            # Use our Clerk authentication backend
            backend = ClerkAuthenticationBackend()
            user = backend.authenticate(request, token=token)
            
            if user:
                return (user, token)
            else:
                raise AuthenticationFailed('Invalid authentication token')
                
        except IndexError:
            raise AuthenticationFailed('Token prefix missing')
        except Exception as e:
            raise AuthenticationFailed(str(e))