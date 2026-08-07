from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'status', 'completion', 'user', 'created_at')
    list_filter = ('type', 'status', 'user')
    search_fields = ('name', 'description', 'technologies')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
