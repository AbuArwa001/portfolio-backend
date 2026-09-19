from rest_framework import serializers
from .models import BlogPost


class BlogPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "subtitle",
            "content",
            "cover_image",
            "source",
            "canonical_url",
            "medium_guid",
            "tags",
            "read_time_minutes",
            "is_published",
            "is_featured",
            "published_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
