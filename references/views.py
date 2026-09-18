from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Reference
from .serializers import ReferenceSerializer, ReferenceSubmissionSerializer


class ReferenceViewSet(viewsets.ModelViewSet):
    serializer_class = ReferenceSerializer

    def get_permissions(self):
        # Public read (list/retrieve) and public submission
        if self.action in ("list", "retrieve", "submit"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "submit":
            return ReferenceSubmissionSerializer
        return ReferenceSerializer

    def get_queryset(self):
        # If user is authenticated admin, allow seeing all references
        if self.request.user and self.request.user.is_authenticated:
            return Reference.objects.all()
        # For public view, only show approved references
        return Reference.objects.filter(is_approved=True)

    @action(detail=False, methods=["post"], permission_classes=[permissions.AllowAny])
    def submit(self, request):
        """Public endpoint allowing referees to submit their details and testimonial."""
        serializer = ReferenceSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Always save as unapproved (pending admin review)
        reference = serializer.save(is_approved=False)
        return Response(
            {
                "message": f"Thank you, {reference.name}! Your endorsement has been submitted successfully and will appear once reviewed.",
                "data": ReferenceSerializer(reference).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def toggle_approval(self, request, pk=None):
        """Authenticated endpoint for admin to toggle approval status."""
        reference = self.get_object()
        reference.is_approved = not reference.is_approved
        reference.save(update_fields=["is_approved"])
        return Response(
            {
                "id": reference.id,
                "is_approved": reference.is_approved,
                "message": f"Reference is now {'approved and published' if reference.is_approved else 'hidden from public view'}.",
            },
            status=status.HTTP_200_OK,
        )
