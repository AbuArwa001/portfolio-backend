from rest_framework import serializers
from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.id')
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'user', 'name', 'description', 'link',
            'status', 'completion', 'technologies', 'type',
            'image', 'image_url', 'created_at',
        ]
        read_only_fields = ('user', 'created_at', 'image_url')

    def get_image_url(self, obj):
        """Return an absolute URL for the image, or None."""
        if not obj.image:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url