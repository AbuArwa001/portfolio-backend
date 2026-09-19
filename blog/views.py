from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import BlogPost
from .serializers import BlogPostSerializer
from .services.medium_sync import sync_medium_posts


class BlogPostViewSet(viewsets.ModelViewSet):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_value_regex = r'[^/]+'

    def get_queryset(self):
        qs = BlogPost.objects.all()
        # Non-staff users only see published posts
        if not (self.request.user and self.request.user.is_authenticated):
            qs = qs.filter(is_published=True)

        # Optional search filter
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(title__icontains=search)
                | Q(subtitle__icontains=search)
                | Q(content__icontains=search)
                | Q(slug__icontains=search)
            )

        # Optional source filter
        source = self.request.query_params.get("source")
        if source:
            qs = qs.filter(source=source)

        # Optional tag filter
        tag = self.request.query_params.get("tag")
        if tag:
            qs = qs.filter(tags__icontains=tag)

        return qs.order_by("-published_at", "-created_at")

    def get_object(self):
        queryset = BlogPost.objects.all()
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_val = self.kwargs.get(lookup_url_kwarg)

        if lookup_val is not None:
            if str(lookup_val).isdigit():
                obj = get_object_or_404(queryset, pk=int(lookup_val))
            else:
                obj = get_object_or_404(queryset, slug=lookup_val)
            self.check_object_permissions(self.request, obj)
            return obj

        return super().get_object()

    @action(detail=False, methods=["get", "post"], permission_classes=[permissions.IsAuthenticatedOrReadOnly])
    def sync_medium(self, request):
        """
        Fetches and synchronizes articles from the Medium RSS feed.
        """
        username = (
            request.data.get("username")
            if hasattr(request, "data") and isinstance(request.data, dict)
            else None
        ) or request.query_params.get("username") or "khalfanathman"

        result = sync_medium_posts(username=username)
        status_code = status.HTTP_200_OK if result.get("success") else status.HTTP_500_INTERNAL_SERVER_ERROR
        return Response(result, status=status_code)
