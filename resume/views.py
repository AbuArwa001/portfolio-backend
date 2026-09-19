import os
import json
from pathlib import Path
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Resume
from .serializers import ResumeSerializer


def get_default_resume_data():
    base_dir = Path(__file__).resolve().parent.parent
    candidates = [
        base_dir.parent / "portfolio" / "app" / "resume" / "resume.json",
        base_dir.parent / "portfolio-admin" / "app" / "resume" / "resume.json",
        base_dir / "resume_data.json",
    ]
    for p in candidates:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("profile") or data.get("experience"):
                        return data
            except Exception:
                pass
    return {}


class ResumeViewSet(viewsets.ModelViewSet):
    queryset = Resume.objects.all()
    serializer_class = ResumeSerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.action in ("list", "retrieve", "primary"):
            if self.request.method in ("GET", "HEAD", "OPTIONS"):
                return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_object(self):
        slug = self.kwargs.get("slug", "primary")
        obj, created = Resume.objects.get_or_create(slug=slug)
        if created or not obj.profile:
            initial = get_default_resume_data()
            if initial:
                obj.profile = initial.get("profile", {})
                obj.contact = initial.get("contact", {})
                obj.experience = initial.get("experience", [])
                obj.education = initial.get("education", [])
                obj.skills = initial.get("skills", [])
                obj.skills_categorized = initial.get("skills_categorized", {})
                obj.projects = initial.get("projects", [])
                obj.certifications = initial.get("certifications", [])
                obj.badges = initial.get("badges", [])
                obj.references = initial.get("references", [])
                obj.save()
        return obj

    @action(detail=False, methods=["get", "put", "patch"])
    def primary(self, request):
        """Dedicated endpoint to fetch or update the primary active resume stored in the database."""
        obj = self.get_object()
        if request.method == "GET":
            return Response(ResumeSerializer(obj).data)

        if not request.user or not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = ResumeSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
