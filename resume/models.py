from django.db import models
from django.conf import settings


class Resume(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="resumes",
    )
    title = models.CharField(max_length=255, default="Primary Curriculum Vitae")
    slug = models.SlugField(max_length=100, default="primary", unique=True)
    profile = models.JSONField(default=dict, blank=True)
    contact = models.JSONField(default=dict, blank=True)
    experience = models.JSONField(default=list, blank=True)
    education = models.JSONField(default=list, blank=True)
    skills = models.JSONField(default=list, blank=True)
    skills_categorized = models.JSONField(default=dict, blank=True)
    projects = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    badges = models.JSONField(default=list, blank=True)
    references = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.title} ({self.slug})"
