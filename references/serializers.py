from rest_framework import serializers
from .models import Reference


class ReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reference
        fields = "__all__"


class ReferenceSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reference
        fields = [
            "id",
            "name",
            "title",
            "company",
            "relationship",
            "quote",
            "email",
            "phone",
            "linkedin",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
