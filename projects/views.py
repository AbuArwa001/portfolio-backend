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
            try:
                specific_user = User.objects.filter(email="khalfan@khalfanathman.dev").first() or \
                                User.objects.filter(username__in=["khalfan", "AbuArwa001", "admin"]).first()
                if specific_user:
                    projects = Project.objects.filter(user=specific_user)
                    if projects.exists():
                        return projects
            except Exception:
                pass
            return Project.objects.all()

    def perform_create(self, serializer):
        """
        Automatically assign the current user to the project when creating
        """
        user = self.request.user if self.request.user.is_authenticated else User.objects.first()
        serializer.save(user=user)

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