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
    badge = models.URLField()
    type = models.CharField(max_length=10, choices=[
        ("aws", "AWS"),
        ("alx", "ALX"),
        ("other", "Other"),
    ])