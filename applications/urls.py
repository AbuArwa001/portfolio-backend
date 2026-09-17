from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobApplicationViewSet, CoverLetterViewSet

router = DefaultRouter()
router.register(r'applications', JobApplicationViewSet, basename='job-application')
router.register(r'letters', CoverLetterViewSet, basename='cover-letter')

urlpatterns = [
    path('', include(router.urls)),
]
