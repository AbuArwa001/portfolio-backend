from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import UserSerializer

User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """Get current authenticated user data"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@api_view(['POST'])
def webhook_handler(request):
    """Handle Clerk webhooks for user sync"""
    # Verify webhook signature (implementation depends on your setup)
    # Handle different webhook types: user.created, user.updated, user.deleted
    
    event_type = request.headers.get('X-Clerk-Event')
    data = request.data
    
    if event_type == 'user.created':
        # Create a new user
        user, created = User.objects.get_or_create(
            clerk_user_id=data['id'],
            defaults={
                'username': data.get('email_addresses', [{}])[0].get('email_address', ''),
                'email': data.get('email_addresses', [{}])[0].get('email_address', ''),
                'first_name': data.get('first_name', ''),
                'last_name': data.get('last_name', ''),
            }
        )
        
    elif event_type == 'user.updated':
        # Update existing user
        try:
            user = User.objects.get(clerk_user_id=data['id'])
            user.email = data.get('email_addresses', [{}])[0].get('email_address', user.email)
            user.first_name = data.get('first_name', user.first_name)
            user.last_name = data.get('last_name', user.last_name)
            user.save()
        except User.DoesNotExist:
            pass
            
    elif event_type == 'user.deleted':
        # Delete user
        try:
            user = User.objects.get(clerk_user_id=data['id'])
            user.delete()
        except User.DoesNotExist:
            pass
    
    return Response(status=status.HTTP_200_OK)