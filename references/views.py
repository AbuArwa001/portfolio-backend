from rest_framework import viewsets, permissions
from .models import Reference
from .serializers import ReferenceSerializer


class ReferenceViewSet(viewsets.ModelViewSet):
    serializer_class = ReferenceSerializer

    def get_permissions(self):
        # Public read (list/retrieve), auth required for writes
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Reference.objects.all()
