from rest_framework import serializers
from .models import JobApplication, CoverLetter

class JobApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = [
            "id",
            "company",
            "role",
            "status",
            "link",
            "done",
            "google_search_link",
            "job_requirements",
            "date_applied",
            "take_by",
            "oa",
            "phone_screen",
            "interview",
            "interview_done",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            validated_data["user"] = request.user
        return super().create(validated_data)


class CoverLetterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoverLetter
        fields = [
            "id",
            "title",
            "company",
            "role",
            "recipient",
            "job_description",
            "tone",
            "include_photo",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            validated_data["user"] = request.user
        return super().create(validated_data)
