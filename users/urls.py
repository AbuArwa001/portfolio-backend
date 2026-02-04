from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CertificationViewSet, SkillViewSet, LanguageViewSet, 
    SkillCategoryViewSet, UserProfileViewSet, UserViewSet
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'profile/certifications', CertificationViewSet, basename='certification')
router.register(r'profile/languages', LanguageViewSet, basename='language')
# router.register(r'profile/skill-categories', SkillCategoryViewSet, basename='skill-category')
# Keeping 'profile/skill-categories' standard:
router.register(r'profile/skill-categories', SkillCategoryViewSet, basename='skill-category')
router.register(r'profile/skills', SkillViewSet, basename='skill')
router.register(r'profile', UserProfileViewSet, basename='profile')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
    # Legacy/Convenience mapping:
    path('me/', UserViewSet.as_view({'get': 'me'}), name='current-user'),
    path('register/', UserViewSet.as_view({'post': 'register'}), name='register-user'),
]
