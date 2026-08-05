from django.db import models

"""
interface CertificationData {
  id: number;
  name: string;
  issuer: string;
  date: string;
  badge: string;
  type: "aws" | "alx" | "other";
}

"""

class Certification(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='certifications'
    )
    name = models.CharField(max_length=255)
    issuer = models.CharField(max_length=255)
    date = models.DateField()
    badge = models.URLField(blank=True, null=True, help_text="URL to badge image (e.g. Credly badge image)")
    credential_url = models.URLField(blank=True, null=True, help_text="URL to verify the credential online")
    in_progress = models.BooleanField(default=False)
    type = models.CharField(max_length=10, choices=[
        ("aws", "AWS"),
        ("alx", "ALX"),
        ("oracle", "Oracle"),
        ("badge", "Badge"),
        ("other", "Other"),
    ])

    def __str__(self):
        return f"{self.name} ({self.issuer})"