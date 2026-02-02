from rest_framework import permissions


class IsAuthenticated(permissions.BasePermission):
    """

    """
    def has_permission(self, request, view):
        return permissions.AllowAny().has_permission(request, view)
    # def has_permission(self, request, view):
    #     return request.user and request.user.is_authenticated