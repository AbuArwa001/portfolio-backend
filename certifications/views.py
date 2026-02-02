
# portfolio-backend/certifications/views.py
from django.shortcuts import render
from rest_framework import viewsets
from .models import Certification
from .serializers import CertificationSerializer
from users.models import User


class CertificationViewSet(viewsets.ModelViewSet):
    queryset = Certification.objects.all()
    serializer_class = CertificationSerializer

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

    # def get_queryset(self):
    #     users = User.objects.all()
    #     user_info = User.objects.prefetch_related('certifications').get(id=self.request.user.id)
    #     # user_info = User.objects.prefetch_related('certifications').get(id=self.request.user.id)
    #     print(users)
    #     return self.queryset.filter(user=user_info)
    def get_queryset(self):
        # If user is authenticated, show their certifications
        if self.request.user.is_authenticated:
            return Certification.objects.filter(user=self.request.user)
        
        # Otherwise, show certifications for the specific email
        try:
            user = User.objects.get(email='khalfan@khalfanathman.dev')
            return Certification.objects.filter(user=user)
        except User.DoesNotExist:
            return Certification.objects.none()