# portfolio-backend/users/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
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

def get_target_user(request):
    """Helper function to get the appropriate user based on authentication"""
    if request.user.is_authenticated:
        return request.user
    else:
        try:
            return User.objects.get(username="AbuArwa001")
        except User.DoesNotExist:
            return None

# ---------------- AUTH & USER ----------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

# users/views.py
@api_view(['POST', 'PATCH', 'PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    print(f"Request user: {request.user}")
    print(f"Request data: {request.data}")
    print(f"Request method: {request.method}")
    
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    # Use the serializer
    serializer = UserProfileSerializer(profile, data=request.data, partial=True)
    
    if serializer.is_valid():
        try:
            serializer.save()
            print("Serializer save successful")
            return Response(serializer.data)
        except Exception as e:
            print(f"Error during save: {e}")
            return Response({'error': str(e)}, status=400)
    
    print("Serializer errors:", serializer.errors)
    return Response(serializer.errors, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_profile_image(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    # Check if file is provided
    if 'profile_image' not in request.FILES:
        return Response({'error': 'No image file provided'}, status=400)
    
    uploaded_file = request.FILES['profile_image']
    
    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if uploaded_file.content_type not in allowed_types:
        return Response({'error': 'Invalid file type. Only images are allowed.'}, status=400)
    
    # Validate file size (max 5MB)
    if uploaded_file.size > 5 * 1024 * 1024:
        return Response({'error': 'File too large. Maximum size is 5MB.'}, status=400)
    
    try:
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_extension = os.path.splitext(uploaded_file.name)[1]
        filename = f"profile_images/user_{request.user.id}_{timestamp}{file_extension}"
        
        # Delete old profile image if it exists
        if profile.profile_image:
            try:
                if os.path.isfile(profile.profile_image.path):
                    os.remove(profile.profile_image.path)
            except (ValueError, OSError):
                # If the file doesn't exist or other issues, just continue
                pass
        
        # Save new image
        profile.profile_image = uploaded_file
        profile.save()
        
        # Return the image URL
        image_url = profile.profile_image.url
        
        return Response({
            'message': 'Profile image uploaded successfully',
            'imageUrl': image_url
        })
        
    except Exception as e:
        return Response({'error': f'Error uploading image: {str(e)}'}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        # Create user
        user = User.objects.create(
            username=serializer.validated_data['username'],
            email=serializer.validated_data['email'],
            first_name=serializer.validated_data.get('first_name', ''),
            last_name=serializer.validated_data.get('last_name', ''),
            password=make_password(serializer.validated_data['password'])
        )
        # Create profile
        UserProfile.objects.create(user=user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_data(request):
    """
    Get user for Portfolio website owner
    """
    try:
        user = User.objects.get(username="AbuArwa001")
        serializer = UserSerializer(user)
        return Response(serializer.data)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)

# ---------------- PROFILE ----------------

@api_view(['GET','POST', 'DELETE'])
@permission_classes([AllowAny])
def get_profile(request):
    target_user = get_target_user(request)
    if not target_user:
        return Response({'error': 'User not found'}, status=404)

    if request.method == 'GET':
        try:
            profile = target_user.profile
            return Response(UserProfileSerializer(profile).data)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=404)

    elif request.method == 'POST':
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        try:
            request.user.profile.delete()
            return Response(status=204)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=404)

# ---------------- CERTIFICATIONS ----------------

# portfolio-backend/users/views.py
@api_view(['GET', 'POST', 'DELETE', 'PATCH'])
@permission_classes([AllowAny])
def manage_certifications(request, cert_id=None):
    target_user = get_target_user(request)
    if not target_user:
        return Response({'error': 'User not found'}, status=404)

    profile = target_user.profile
    
    if request.method == 'GET':
        if cert_id:
            try:
                # FIXED: Check if certification belongs to user's profile
                cert = profile.certifications.get(id=cert_id)
                return Response(CertificationSerializer(cert).data)
            except Certification.DoesNotExist:
                return Response({'error': 'Certification not found'}, status=404)

        certifications = profile.certifications.all()
        return Response(CertificationSerializer(certifications, many=True).data)

    elif request.method == 'POST':
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        
        serializer = CertificationSerializer(data=request.data)
        if serializer.is_valid():
            cert = serializer.save()
            request.user.profile.certifications.add(cert)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
    elif request.method == 'PATCH' and cert_id:
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        
        try:
            # FIXED: Check if certification belongs to user's profile
            cert = request.user.profile.certifications.get(id=cert_id)
            serializer = CertificationSerializer(cert, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=400)
        except Certification.DoesNotExist:
            return Response({'error': 'Certification not found'}, status=404)

    elif request.method == 'DELETE' and cert_id:
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        
        try:
            # FIXED: Check if certification belongs to user's profile
            cert = request.user.profile.certifications.get(id=cert_id)
            request.user.profile.certifications.remove(cert)
            # Don't delete the certification object itself as it might be used by others
            return Response(status=204)
        except Certification.DoesNotExist:
            return Response({'error': 'Certification not found'}, status=404)

# ---------------- SKILLS ----------------

@api_view(['GET','POST', 'DELETE'])
@permission_classes([AllowAny])
def manage_skills(request, skill_id=None):
    target_user = get_target_user(request)
    if not target_user:
        return Response({'error': 'User not found'}, status=404)

    profile = target_user.profile
    
    if request.method == 'GET':
        if skill_id:
            try:
                skill = Skill.objects.get(id=skill_id)
                return Response(SkillSerializer(skill).data)
            except Skill.DoesNotExist:
                return Response({'error': 'Skill not found'}, status=404)
        
        # FIXED: Get skills through categories
        user_categories = profile.skill_categories.all()
        skills = Skill.objects.filter(category__in=user_categories)
        return Response(SkillSerializer(skills, many=True).data)

    elif request.method == 'POST':
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        
        serializer = SkillSerializer(data=request.data)
        if serializer.is_valid():
            skill = serializer.save()
            # Note: You might want to add the category to user's profile
            # if it's not already there
            if skill.category not in request.user.profile.skill_categories.all():
                request.user.profile.skill_categories.add(skill.category)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE' and skill_id:
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        
        try:
            skill = Skill.objects.get(id=skill_id)
            # Check if this skill belongs to the user's categories
            if skill.category in request.user.profile.skill_categories.all():
                skill.delete()
                return Response(status=204)
            else:
                return Response({'error': 'Skill not found in your categories'}, status=404)
        except Skill.DoesNotExist:
            return Response({'error': 'Skill not found'}, status=404)

@api_view(['GET'])
@permission_classes([AllowAny])
def manage_skill_categories(request, category_id=None):
    target_user = get_target_user(request)
    if not target_user:
        return Response({'error': 'User not found'}, status=404)

    profile = target_user.profile
    if category_id:
        try:
            category = SkillCategory.objects.get(id=category_id)
            return Response(SkillCategorySerializer(category).data)
        except SkillCategory.DoesNotExist:
            return Response({'error': 'Skill category not found'}, status=404)
    return Response(SkillCategorySerializer(profile.skill_categories.all(), many=True).data)

# ---------------- LANGUAGES ----------------

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([AllowAny])
def manage_languages(request, language_id=None):
    target_user = get_target_user(request)
    if not target_user:
        return Response({'error': 'User not found'}, status=404)

    profile = target_user.profile
    
    if request.method == 'GET':
        if language_id:
            try:
                language = Language.objects.get(id=language_id)
                return Response(LanguageSerializer(language).data)
            except Language.DoesNotExist:
                return Response({'error': 'Language not found'}, status=404)
        return Response(LanguageSerializer(profile.languages.all(), many=True).data)

    elif request.method == 'POST':
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        serializer = LanguageSerializer(data=request.data)
        if serializer.is_valid():
            language = serializer.save()
            request.user.profile.languages.add(language)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        language_id = request.data.get('id')
        try:
            language = Language.objects.get(id=language_id)
            request.user.profile.languages.remove(language)
            return Response(status=204)
        except Language.DoesNotExist:
            return Response({'error': 'Language not found'}, status=404)

# ---------------- BULK UPDATES ----------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_update_skills(request):
    profile = request.user.profile
    data = request.data
    if not isinstance(data, list):
        return Response({"error": "Expected a list of skill categories"}, status=400)
    profile.skill_categories.clear()
    for category_data in data:
        category, _ = SkillCategory.objects.get_or_create(name=category_data['category'])
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_update_certifications(request):
    profile = request.user.profile
    data = request.data
    
    if not isinstance(data, list):
        return Response({"error": "Expected a list of certifications"}, status=400)
    
    profile.certifications.clear()
    
    for cert_data in data:
        in_progress = cert_data.get('inProgress', cert_data.get('in_progress', False))
        
        cert, created = Certification.objects.get_or_create(
            title=cert_data['title'],
            issuer=cert_data['issuer'],
            defaults={
                'date': cert_data['date'],
                'in_progress': in_progress,
                'type': cert_data.get('type', 'other'),
                'badge': cert_data.get('badge', ''),
                'user': request.user  # Set the user who created it
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_update_languages(request):
    profile = request.user.profile
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
