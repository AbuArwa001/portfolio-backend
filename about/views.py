from rest_framework import viewsets
from .models import About
from .serializers import AboutSerializer

class AboutViewSet(viewsets.ModelViewSet):
    queryset = About.objects.all()
    serializer_class = AboutSerializer
