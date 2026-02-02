from django.shortcuts import render
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Project
from .serializers import ProjectSerializer
from users.models import User

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Project.objects.filter(user=self.request.user)
        else:
            # Use specific user or default to user ID 2 if not found
            try:
                specific_user = User.objects.get(email="khalfan@khalfanathman.dev")
                return Project.objects.filter(user=specific_user)
            except User.DoesNotExist:
                # Fallback to user ID 2 if specific user doesn't exist
                return Project.objects.filter(user_id=2)
    def perform_create(self, serializer):
        """
        Automatically assign the current user to the project when creating
        """
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        """
        Ensure users can only update their own projects
        """
        instance = self.get_object()
        
        # Check if the user owns the project
        if instance.user != request.user:
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Ensure users can only delete their own projects
        """
        instance = self.get_object()
        
        # Check if the user owns the project
        if instance.user != request.user:
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)