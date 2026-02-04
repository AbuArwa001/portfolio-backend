
#backend/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from about.views import AboutViewSet
from projects.views import ProjectViewSet
from blog.views import BlogPostViewSet
from contact.views import ContactMessageViewSet
from django.conf import settings
from django.conf.urls.static import static
from certifications.views import CertificationViewSet

router = routers.DefaultRouter()
router.register(r'about', AboutViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r'blog', BlogPostViewSet)
router.register(r'contact', ContactMessageViewSet)
router.register(r'certifications', CertificationViewSet)

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Portfolio API",
        default_version='v1',
        description="API for Personal Portfolio",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@khalfanathman.dev"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/', include('users.urls')),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)