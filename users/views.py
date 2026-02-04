from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .models import Certification, Language, Skill, SkillCategory, UserProfile
from .serializers import (
    LanguageSerializer,
    SkillCategorySerializer,
    SkillSerializer,
    UserSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
    CertificationSerializer,
)
import os
from datetime import datetime

User = get_user_model()

class BaseProfileViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet handling the logic for retrieval:
    - If authenticated, return current user's items.
    - If anonymous, return 'AbuArwa001' items (Public Portfolio Mode).
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_target_user(self):
        if self.request.user.is_authenticated:
            return self.request.user
        try:
            return User.objects.get(username="AbuArwa001")
        except User.DoesNotExist:
            return None

    def get_profile(self):
        user = self.get_target_user()
        if not user:
            return None
        try:
            return user.profile
        except UserProfile.DoesNotExist:
             if user == self.request.user:
                 return UserProfile.objects.create(user=user)
             return None

class CertificationViewSet(BaseProfileViewSet):
    serializer_class = CertificationSerializer
    
    def get_queryset(self):
        profile = self.get_profile()
        if not profile:
            return Certification.objects.none()
        return profile.certifications.all()

    def perform_create(self, serializer):
        cert = serializer.save(user=self.request.user)
        self.request.user.profile.certifications.add(cert)

    @action(detail=False, methods=['post'], url_path='bulk-update')
    def bulk_update(self, request):
        profile = self.request.user.profile
        data = request.data
        
        if not isinstance(data, list):
            return Response({"error": "Expected a list of certifications"}, status=400)
        
        # Clear existing? Original code did clear.
        profile.certifications.clear()
        
        for cert_data in data:
            in_progress = cert_data.get('inProgress', cert_data.get('in_progress', False))
            
            # Use get_or_create to avoid duplicates if title/issuer matches
            cert, created = Certification.objects.get_or_create(
                title=cert_data['title'],
                issuer=cert_data['issuer'],
                defaults={
                    'date': cert_data['date'],
                    'in_progress': in_progress,
                    'type': cert_data.get('type', 'other'),
                    'badge': cert_data.get('badge', ''),
                    'user': request.user
                }
            )
            
            if not created:
                cert.date = cert_data['date']
                cert.in_progress = in_progress
                cert.type = cert_data.get('type', 'other')
                cert.badge = cert_data.get('badge', '')
                cert.save()
            
            profile.certifications.add(cert)
        
        return Response({'status': 'Certifications updated successfully'})

    def perform_destroy(self, instance):
        # Remove from profile but don't delete object if we want to keep it generic?
        # The original code removed it from profile. 
        self.request.user.profile.certifications.remove(instance)
        # Note: Original code didn't delete the object. 
        # But for full CRUD usually we delete. I'll stick to original behavior (remove relationship)
        # OR better, since these seem personal, we should delete them? 
        # Existing code: request.user.profile.certifications.remove(cert) then 204.
        pass 

class LanguageViewSet(BaseProfileViewSet):
    serializer_class = LanguageSerializer

    def get_queryset(self):
        profile = self.get_profile()
        if not profile:
            return Language.objects.none()
        return profile.languages.all()

    def perform_create(self, serializer):
        lang = serializer.save()
        self.request.user.profile.languages.add(lang)

    @action(detail=False, methods=['post'], url_path='bulk-update')
    def bulk_update(self, request):
        profile = self.request.user.profile
        data = request.data
        if not isinstance(data, list):
            return Response({"error": "Expected a list of languages"}, status=400)
        
        profile.languages.clear()
        for lang_data in data:
            lang, _ = Language.objects.get_or_create(
                name=lang_data['name'],
                proficiency=lang_data['proficiency']
            )
            profile.languages.add(lang)
        return Response({'status': 'Languages updated successfully'})

class SkillCategoryViewSet(BaseProfileViewSet):
    serializer_class = SkillCategorySerializer

    def get_queryset(self):
        profile = self.get_profile()
        if not profile:
            return SkillCategory.objects.none()
        return profile.skill_categories.all()

    @action(detail=False, methods=['post'], url_path='bulk-update')
    def bulk_update(self, request):
        profile = self.request.user.profile
        data = request.data
        if not isinstance(data, list):
            return Response({"error": "Expected a list of skill categories"}, status=400)
        
        profile.skill_categories.clear() # Maybe dangerous if multiple sessions? But consistent with old code.
        
        for category_data in data:
            category, _ = SkillCategory.objects.get_or_create(name=category_data['category'])
            
            # Handle skills within category
            if 'skills' in category_data:
                for skill_data in category_data['skills']:
                     skill, created = Skill.objects.get_or_create(
                        name=skill_data['name'],
                        category=category,
                        defaults={'level': skill_data['level']}
                     )
                     if not created:
                         skill.level = skill_data['level']
                         skill.save()
            
            profile.skill_categories.add(category)
        return Response({'status': 'Skills updated successfully'})

class SkillViewSet(BaseProfileViewSet):
    serializer_class = SkillSerializer

    def get_queryset(self):
        profile = self.get_profile()
        if not profile:
            return Skill.objects.none()
        
        # Original logic: return skills that belong to the categories the user has
        user_categories = profile.skill_categories.all()
        return Skill.objects.filter(category__in=user_categories)

    def perform_create(self, serializer):
        skill = serializer.save()
        if skill.category not in self.request.user.profile.skill_categories.all():
            self.request.user.profile.skill_categories.add(skill.category)

class UserProfileViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def list(self, request):
        # Handles GET /api/auth/profile/
        user = request.user if request.user.is_authenticated else None
        if not user:
            try:
                user = User.objects.get(username="AbuArwa001")
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=404)
        
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            if request.user.is_authenticated and user == request.user:
                profile = UserProfile.objects.create(user=user)
            else:
                return Response({'error': 'Profile not found'}, status=404)
        
        return Response(UserProfileSerializer(profile).data)

    def create(self, request):
        # Handles POST /api/auth/profile/
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    @action(detail=False, methods=['delete'])
    def remove(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        try:
            request.user.profile.delete()
            return Response(status=204)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=404)

    @action(detail=False, methods=['post'], url_path='upload-image')
    def upload_image(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        
        if 'profile_image' not in request.FILES:
            return Response({'error': 'No image file provided'}, status=400)
        
        uploaded_file = request.FILES['profile_image']
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if uploaded_file.content_type not in allowed_types:
             return Response({'error': 'Invalid file type.'}, status=400)
        
        if uploaded_file.size > 5 * 1024 * 1024:
            return Response({'error': 'File too large.'}, status=400)

        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        
        # Logic to delete old image
        if profile.profile_image:
             try:
                 if os.path.isfile(profile.profile_image.path):
                     os.remove(profile.profile_image.path)
             except Exception:
                 pass
        
        profile.profile_image = uploaded_file
        profile.save()
        return Response({'message': 'Profile image uploaded successfully', 'imageUrl': profile.profile_image.url})


    @action(detail=False, methods=['post'], url_path='update')
    def update_profile_custom(self, request):
        # Supports the /api/auth/profile/update/ endpoint
        return self.create(request)


class UserViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'])
    def me(self, request):
        if not request.user.is_authenticated:
             return Response({'error': 'Authentication required'}, status=401)
        return Response(UserSerializer(request.user).data)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.create_user(
                username=serializer.validated_data['username'],
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
                first_name=serializer.validated_data.get('first_name', ''),
                last_name=serializer.validated_data.get('last_name', '')
            )
            UserProfile.objects.create(user=user)
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

