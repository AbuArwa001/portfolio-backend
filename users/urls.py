
# portfolio-backend/users/urls.py
from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    path('me/', views.get_current_user, name='current-user'),
    path('profile/update/', views.update_profile, name='update-profile'),
    path('profile/', views.get_profile, name='get-profile'),
    path('profile/upload-image/', views.upload_profile_image, name='upload-profile-image'),
    path('profile/skills/', views.manage_skills, name='manage_skills'),
    path('profile/skill-categories/', views.manage_skill_categories, name='manage_skill_categories'),
    path('profile/skill-categories/<int:category_id>/', views.manage_skill_categories, name='manage_skill_categories_with_id'),
    path('profile/certifications/', views.manage_certifications, name='manage_certifications'),  # Make cert_id optional
    path('profile/certifications/<int:cert_id>/', views.manage_certifications, name='manage_certifications_with_id'),
    path('profile/skills/<int:skill_id>/', views.manage_skills, name='manage_skills_with_id'),
    path('profile/languages/', views.manage_languages, name='manage_languages'),
    path('profile/languages/<int:language_id>/', views.manage_languages, name='manage_languages_with_id'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', views.register_user, name='register-user'),
    path('profile/bulk/skills/', views.bulk_update_skills, name='bulk_update_skills'),
    path('profile/bulk/certifications/', views.bulk_update_certifications, name='bulk_update_certifications'),
    path('profile/bulk/languages/', views.bulk_update_languages, name='bulk_update_languages'),
]

