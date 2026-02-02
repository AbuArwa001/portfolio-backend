from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    
    def __str__(self):
        return self.email

class SkillCategory(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Skill(models.Model):
    name = models.CharField(max_length=100)
    level = models.IntegerField(default=0)  # 0-100 percentage
    category = models.ForeignKey(SkillCategory, on_delete=models.CASCADE, related_name='skills')
    
    def __str__(self):
        return f"{self.name} ({self.level}%)"

class Certification(models.Model):
    """
    Represents a user's certification.
    CertificationData {
        id: number;
        name: string;
        issuer: string;
        date: string;
        badge: string;
        type: "aws" | "alx" | "other";
        }
    """
    title = models.CharField(max_length=200)
    issuer = models.CharField(max_length=200)
    date = models.CharField(max_length=20)
    badge = models.CharField(max_length=200, default='', blank=True)
    type = models.CharField(max_length=20, choices=[
        ('aws', 'AWS'),
        ('alx', 'ALX'),
        ('other', 'Other'),
    ],
    
    default='other'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='certifications_created')
    in_progress = models.BooleanField(default=False)

    
    def __str__(self):
        status = " (In Progress)" if self.in_progress else ""
        return f"{self.title} by {self.issuer}{status}"

class Language(models.Model):
    PROFICIENCY_CHOICES = [
        ('Native', 'Native'),
        ('Fluent', 'Fluent'),
        ('Proficient', 'Proficient'),
        ('Intermediate', 'Intermediate'),
        ('Basic', 'Basic'),
    ]
    
    name = models.CharField(max_length=100)
    proficiency = models.CharField(max_length=20, choices=PROFICIENCY_CHOICES)
    
    def __str__(self):
        return f"{self.name} ({self.proficiency})"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    title = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    github = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    # Relationships to other models
    skill_categories = models.ManyToManyField(SkillCategory, blank=True)
    certifications = models.ManyToManyField(Certification, blank=True)
    languages = models.ManyToManyField(Language, blank=True)
    
    def __str__(self):
        return f"{self.user.email}'s Profile"