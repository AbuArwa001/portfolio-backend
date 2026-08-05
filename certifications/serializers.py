from rest_framework import serializers
from .models import Certification


class CertificationSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.id')

    class Meta:
        model = Certification
        fields = [
            'id', 'user', 'name', 'issuer', 'date',
            'badge', 'credential_url', 'in_progress', 'type',
        ]
