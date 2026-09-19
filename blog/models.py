from django.db import models
from django.utils.text import slugify
from django.utils import timezone


class BlogPost(models.Model):
    SOURCE_CHOICES = [
        ('manual', 'Manual'),
        ('medium', 'Medium'),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    subtitle = models.TextField(blank=True, default='', help_text='Short description / excerpt')
    content = models.TextField(help_text='Full article content in Markdown or HTML')
    cover_image = models.URLField(max_length=1000, blank=True, default='', help_text='Header / preview image URL')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    canonical_url = models.URLField(max_length=1000, blank=True, null=True, help_text='Link to original article (e.g. on Medium)')
    medium_guid = models.CharField(max_length=255, blank=True, null=True, unique=True, help_text='Medium RSS GUID for deduplication')
    tags = models.JSONField(default=list, blank=True, help_text='List of tags/categories')
    read_time_minutes = models.PositiveIntegerField(default=3, help_text='Estimated read time in minutes')
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or 'article'
            slug = base_slug
            counter = 1
            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        if not self.published_at and self.is_published:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
