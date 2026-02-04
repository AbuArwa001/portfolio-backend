import json
import os
import sys
import django
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from users.models import User, UserProfile, SkillCategory, Skill, Certification, Language
from projects.models import Project

def populate_db(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    # 1. Create/Update User
    profile_data = data.get('profile', {})
    user, created = User.objects.get_or_create(
        email=profile_data['email'],
        defaults={
            'username': profile_data['username'],
            'first_name': profile_data['first_name'],
            'last_name': profile_data['last_name'],
        }
    )
    if not created:
        user.first_name = profile_data['first_name']
        user.last_name = profile_data['last_name']
        user.save()
    else:
        user.set_password("password123") # Default password
        user.save()
        print(f"Created user {user.username}")

    # 2. Update Profile
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.title = profile_data.get('title', '')
    profile.bio = profile_data.get('bio', '')
    profile.location = profile_data.get('location', '')
    profile.phone = profile_data.get('phone', '')
    profile.linkedin = profile_data.get('linkedin', '')
    profile.github = profile_data.get('github', '')
    profile.website = profile_data.get('website', '')
    profile.save()
    print("Updated User Profile")

    # 3. Skills
    Skill.objects.all().delete() # Optional: Clear old skills to avoid duplicates if re-running
    SkillCategory.objects.all().delete() 
    
    for cat_data in data.get('skill_categories', []):
        category, _ = SkillCategory.objects.get_or_create(name=cat_data['name'])
        profile.skill_categories.add(category)
        
        for skill_data in cat_data.get('skills', []):
            Skill.objects.create(
                name=skill_data['name'],
                level=skill_data['level'],
                category=category
            )
    print("Imported Skills")

    # 4. Certifications
    Certification.objects.filter(user=user).delete() # Clear old imports
    for cert_data in data.get('certifications', []):
        cert = Certification.objects.create(
            user=user,
            title=cert_data['title'],
            issuer=cert_data['issuer'],
            date=cert_data.get('date', ''),
            type=cert_data.get('type', 'other'),
            in_progress=cert_data.get('in_progress', False)
        )
        profile.certifications.add(cert)
    print("Imported Certifications")

    # 5. Projects
    Project.objects.filter(user=user).delete()
    for proj_data in data.get('projects', []):
        Project.objects.create(
            user=user,
            name=proj_data['name'],
            description=proj_data['description'],
            technologies=proj_data['technologies'],
            status=proj_data.get('status', 'completed'),
            completion=proj_data.get('completion', '100%'),
            type=proj_data.get('type', 'web'),
            link=proj_data.get('link', '')
        )
    print("Imported Projects")
    
    # 6. Default Languages (as resume mentions them)
    Language.objects.all().delete()
    langs = [
        {'name': 'English', 'proficiency': 'Fluent'},
        {'name': 'Arabic', 'proficiency': 'Proficient'},
        {'name': 'Swahili', 'proficiency': 'Native'},
    ]
    for lang in langs:
        l = Language.objects.create(name=lang['name'], proficiency=lang['proficiency'])
        profile.languages.add(l)
    print("Imported Languages")

if __name__ == '__main__':
    json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resume_data.json')
    populate_db(json_path)
