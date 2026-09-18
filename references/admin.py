from django.contrib import admin
from .models import Reference


@admin.register(Reference)
class ReferenceAdmin(admin.ModelAdmin):
    list_display = ("name", "title", "company", "relationship", "is_approved", "created_at")
    list_filter = ("is_approved", "company", "created_at")
    search_fields = ("name", "title", "company", "relationship", "quote", "email")
    actions = ["approve_references", "unapprove_references"]

    @admin.action(description="Approve selected references for public display")
    def approve_references(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description="Hide selected references from public display")
    def unapprove_references(self, request, queryset):
        queryset.update(is_approved=False)
