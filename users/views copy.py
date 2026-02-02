
# portfolio-backend/users/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from .models import Certification, Language, Skill, SkillCategory, UserProfile
from .serializers import LanguageSerializer, SkillCategorySerializer, SkillSerializer, UserSerializer, UserProfileSerializer, UserRegistrationSerializer, CertificationSerializer

User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    serializer = UserProfileSerializer(profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
        
        # Return user data
        user_serializer = UserSerializer(user)
        return Response(user_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_data(request):
    """
    Get user for Portfolio website owner
    """
    user = User.objects.get(username="AbuArwa001")
    serializer = UserSerializer(user)
    return Response(serializer.data)

@api_view(['GET','POST', 'DELETE'])
def get_profile(request):

    if request.method == 'GET':
        try:
            user = User.objects.get(username="AbuArwa001")
            profile = user.profile
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=404)

    elif request.method == 'POST':
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)

        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        try:
            profile = request.user.profile
            profile.delete()
            return Response(status=204)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=404)

# For adding/removing certifications
@api_view(['GET', 'POST', 'DELETE', 'PATCH'])
def manage_certifications(request, cert_id=None):
    profile = User.objects.get(username="AbuArwa001").profile
    # profile = request.user.profile
    if request.method == 'GET':
        if cert_id:
            try:
                cert = Certification.objects.get(id=cert_id)
                serializer = CertificationSerializer(cert)
                return Response(serializer.data)
            except Certification.DoesNotExist:
                return Response({'error': 'Certification not found'}, status=404)

        certifications = profile.certifications.all()
        serializer = CertificationSerializer(certifications, many=True)
        return Response(serializer.data)

    if request.method == 'POST' and permission_classes([IsAuthenticated]):
        # Add new certification
        serializer = CertificationSerializer(data=request.data)
        if serializer.is_valid():
            cert = serializer.save()
            profile.certifications.add(cert)
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    if request.method == 'PATCH' and cert_id and permission_classes([IsAuthenticated]):
        cert = Certification.objects.get(id=cert_id)
        serializer = CertificationSerializer(cert, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE' and cert_id and permission_classes([IsAuthenticated]):
        # Remove certification
        try:
            cert = Certification.objects.get(id=cert_id)
            profile.certifications.remove(cert)
            return Response(status=204)
        except Certification.DoesNotExist:
            return Response({'error': 'Certification not found'}, status=404)

@api_view(['GET','POST', 'DELETE'])
def manage_skills(request, skill_id=None):

    profile = User.objects.get(username="AbuArwa001").profile
    if request.method == 'GET':
        if skill_id:
            try:
                skill = SkillCategory.objects.get(id=skill_id)
                serializer = SkillCategorySerializer(skill)
                return Response(serializer.data)
            except SkillCategory.DoesNotExist:
                return Response({'error': 'Skill category not found'}, status=404)
        skills = profile.skill_categories.all()
        serializer = SkillCategorySerializer(skills, many=True)
        return Response(serializer.data)

    if request.method == 'POST' and permission_classes([IsAuthenticated]):
        
        # Add new skill
        serializer = SkillSerializer(data=request.data)
        if serializer.is_valid():
            skill = serializer.save()
            profile.skills.add(skill)
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE' and skill_id and permission_classes([IsAuthenticated]):
        # Remove skill
        try:
            skill = Skill.objects.get(id=skill_id)
            profile.skills.remove(skill)
            return Response(status=204)
        except Skill.DoesNotExist:
            return Response({'error': 'Skill not found'}, status=404)

@api_view(['GET'])
def manage_skill_categories(request, category_id=None):
    profile = User.objects.get(username="AbuArwa001").profile
    if request.method == 'GET':
        if category_id:
            try:
                category = SkillCategory.objects.get(id=category_id)
                serializer = SkillCategorySerializer(category)
                return Response(serializer.data)
            except SkillCategory.DoesNotExist:
                return Response({'error': 'Skill category not found'}, status=404)
        categories = profile.skill_categories.all()
        serializer = SkillCategorySerializer(categories, many=True)
        return Response(serializer.data)

@api_view(['GET', 'POST', 'DELETE'])
def manage_languages(request, language_id=None):
    profile = User.objects.get(username="AbuArwa001").profile
    if request.method == 'GET':
        if language_id:
            try:
                language = Language.objects.get(id=language_id)
                serializer = LanguageSerializer(language)
                return Response(serializer.data)
            except Language.DoesNotExist:
                return Response({'error': 'Language not found'}, status=404)
        languages = profile.languages.all()
        serializer = LanguageSerializer(languages, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        # Add new language
        serializer = LanguageSerializer(data=request.data)
        if serializer.is_valid():
            language = serializer.save()
            profile.languages.add(language)
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        # Remove language
        language_id = request.data.get('id')
        try:
            language = Language.objects.get(id=language_id)
            profile.languages.remove(language)
            return Response(status=204)
        except Language.DoesNotExist:
            return Response({'error': 'Language not found'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_update_skills(request):
    """
    Bulk update skills with categories and nested skills
    """
    profile = request.user.profile
    data = request.data
    
    # Check if data is a list
    if not isinstance(data, list):
        return Response(
            {"error": "Expected a list of skill categories"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Clear existing skills and categories for this user
    profile.skill_categories.clear()
    
    for category_data in data:
        # Get or create the skill category
        category, created = SkillCategory.objects.get_or_create(
            name=category_data['category']
        )
        
        # Create or update skills in this category
        for skill_data in category_data['skills']:
            skill, created = Skill.objects.get_or_create(
                name=skill_data['name'],
                category=category,
                defaults={'level': skill_data['level']}
            )
            if not created:
                skill.level = skill_data['level']
                skill.save()
        
        # Add category to user's profile
        profile.skill_categories.add(category)
    
    return Response({'status': 'Skills updated successfully'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_update_certifications(request):
    """
    Bulk update certifications
    """
    profile = request.user.profile
    data = request.data
    
    if not isinstance(data, list):
        return Response(
            {"error": "Expected a list of certifications"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    profile.certifications.clear()
    
    for cert_data in data:
        # Handle both 'inProgress' and 'in_progress' field names
        in_progress = cert_data.get('inProgress', cert_data.get('in_progress', False))
        
        cert, created = Certification.objects.get_or_create(
            title=cert_data['title'],
            issuer=cert_data['issuer'],
            defaults={
                'date': cert_data['date'],
                'in_progress': in_progress
            }
        )
        profile.certifications.add(cert)
    
    return Response({'status': 'Certifications updated successfully'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_update_languages(request):
    """
    Bulk update languages
    """
    profile = request.user.profile
    data = request.data
    
    if not isinstance(data, list):
        return Response(
            {"error": "Expected a list of languages"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    profile.languages.clear()
    
    for lang_data in data:
        lang, created = Language.objects.get_or_create(
            name=lang_data['name'],
            proficiency=lang_data['proficiency']
        )
        profile.languages.add(lang)
    
    return Response({'status': 'Languages updated successfully'})