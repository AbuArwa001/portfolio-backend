from django.db import models
from django.conf import settings
import re

def project_image_upload_path(instance, filename):
    # Sanitize project name for safe folder name
    project_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', instance.name)
    if not project_name:
        project_name = 'unnamed_project'
    return f"{project_name}/{filename}"

class Project(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='projects'
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    link = models.URLField(blank=True, null=True)
    status = models.CharField(max_length=100)
    completion = models.CharField(max_length=100)
    technologies = models.CharField(max_length=200)
    type = models.CharField(max_length=100)
    image = models.ImageField(upload_to=project_image_upload_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name