from django.contrib import admin
from .models import (
    StudyCertification,
    Topic,
    Lab,
    LabAttempt,
    Question,
    ExamSession,
    ExamAnswer,
    Flashcard,
    StudyNote,
    Organization,
    InterviewBrief,
    MockInterview,
    StudyLog,
    StudyGoal,
)


@admin.register(StudyCertification)
class StudyCertificationAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "vendor", "exam_code", "is_active"]
    search_fields = ["code", "name", "exam_code"]


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ["certification", "domain_number", "order", "name", "blueprint_ref"]
    list_filter = ["certification", "domain_number"]
    search_fields = ["name", "description", "blueprint_ref"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Lab)
class LabAdmin(admin.ModelAdmin):
    list_display = ["title", "topic", "difficulty", "estimated_time_minutes", "free_tier_eligible"]
    list_filter = ["difficulty", "topic__certification", "free_tier_eligible"]
    search_fields = ["title", "objectives"]
    prepopulated_fields = {"slug": ("title",)}


@admin.register(LabAttempt)
class LabAttemptAdmin(admin.ModelAdmin):
    list_display = ["user", "lab", "status", "time_spent_seconds", "completed_at"]
    list_filter = ["status"]
    search_fields = ["user__email", "lab__title"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["id", "certification", "topic", "question_type", "difficulty", "source", "is_favorite"]
    list_filter = ["certification", "question_type", "difficulty", "source", "is_favorite", "is_reported"]
    search_fields = ["text", "explanation"]


@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "certification", "mode", "score_pct", "passed", "is_completed", "started_at"]
    list_filter = ["certification", "mode", "passed", "is_completed"]


@admin.register(ExamAnswer)
class ExamAnswerAdmin(admin.ModelAdmin):
    list_display = ["id", "session", "question", "is_correct", "flagged_for_review"]
    list_filter = ["is_correct", "flagged_for_review"]


@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "topic", "repetition_level", "interval_days", "ease_factor", "due_date"]
    list_filter = ["topic__certification"]


@admin.register(StudyNote)
class StudyNoteAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "topic", "is_mistake_journal", "created_at"]
    list_filter = ["is_mistake_journal", "topic__certification"]
    search_fields = ["title", "content"]


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["company_name", "role", "status", "application_date", "interview_date"]
    list_filter = ["status"]
    search_fields = ["company_name", "role"]


@admin.register(InterviewBrief)
class InterviewBriefAdmin(admin.ModelAdmin):
    list_display = ["organization", "created_at"]


@admin.register(MockInterview)
class MockInterviewAdmin(admin.ModelAdmin):
    list_display = ["organization", "user", "overall_score", "is_completed", "created_at"]


@admin.register(StudyLog)
class StudyLogAdmin(admin.ModelAdmin):
    list_display = ["user", "certification", "session_type", "duration_minutes", "date"]
    list_filter = ["session_type", "certification"]


@admin.register(StudyGoal)
class StudyGoalAdmin(admin.ModelAdmin):
    list_display = ["user", "certification", "target_exam_date", "daily_goal_minutes", "is_active"]
