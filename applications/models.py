from django.db import models
from django.conf import settings

class JobApplication(models.Model):
    STATUS_CHOICES = [
        ("Applied", "Applied"),
        ("Not yet Applied", "Not yet Applied"),
        ("Interviewing", "Interviewing"),
        ("Offer", "Offer"),
        ("Rejected", "Rejected"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_applications",
        null=True,
        blank=True,
    )
    company = models.CharField(max_length=255)
    role = models.CharField(max_length=255, default="Network / Software Engineer")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Applied")
    link = models.URLField(max_length=1000, blank=True, default="")
    done = models.BooleanField(default=False)
    google_search_link = models.CharField(max_length=1000, blank=True, default="")
    job_requirements = models.TextField(blank=True, default="")
    date_applied = models.DateField(null=True, blank=True)
    
    # Interview Tracking
    take_by = models.CharField(max_length=255, blank=True, default="")
    oa = models.BooleanField(default=False, verbose_name="Online Assessment")
    phone_screen = models.BooleanField(default=False, verbose_name="Phone Screen")
    interview = models.BooleanField(default=False, verbose_name="Interview")
    interview_done = models.BooleanField(default=False, verbose_name="Interview Done")
    notes = models.TextField(blank=True, default="")
    
    # Complete Job Application Tracker Format Fields
    advert_ref = models.CharField(max_length=255, blank=True, default="", verbose_name="Advert Ref / Grade")
    key_responsibilities = models.TextField(blank=True, default="", verbose_name="Key Responsibilities")
    shortlisted = models.BooleanField(default=False, verbose_name="Shortlisted?")
    closing_date = models.DateField(null=True, blank=True, verbose_name="Closing Date")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_applied", "-created_at"]

    def __str__(self):
        return f"{self.company} - {self.role} ({self.status})"


class CoverLetter(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cover_letters",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    recipient = models.CharField(max_length=255, blank=True, default="Hiring Manager")
    job_description = models.TextField(blank=True, default="")
    tone = models.CharField(max_length=50, default="executive")
    include_photo = models.BooleanField(default=False)
    content = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.company}"
