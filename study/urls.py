from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StudyCertificationViewSet,
    TopicViewSet,
    LabViewSet,
    LabAttemptViewSet,
    QuestionViewSet,
    ExamSessionViewSet,
    ExamAnswerViewSet,
    FlashcardViewSet,
    StudyNoteViewSet,
    OrganizationViewSet,
    InterviewBriefViewSet,
    MockInterviewViewSet,
    StudyLogViewSet,
    StudyGoalViewSet,
    PublicStudyBadgeView,
)

router = DefaultRouter()
router.register(r"certifications", StudyCertificationViewSet, basename="study-certification")
router.register(r"topics", TopicViewSet, basename="study-topic")
router.register(r"labs", LabViewSet, basename="study-lab")
router.register(r"lab-attempts", LabAttemptViewSet, basename="study-lab-attempt")
router.register(r"questions", QuestionViewSet, basename="study-question")
router.register(r"exam-sessions", ExamSessionViewSet, basename="study-exam-session")
router.register(r"exam-answers", ExamAnswerViewSet, basename="study-exam-answer")
router.register(r"flashcards", FlashcardViewSet, basename="study-flashcard")
router.register(r"notes", StudyNoteViewSet, basename="study-note")
router.register(r"organizations", OrganizationViewSet, basename="study-organization")
router.register(r"interview-briefs", InterviewBriefViewSet, basename="study-interview-brief")
router.register(r"mock-interviews", MockInterviewViewSet, basename="study-mock-interview")
router.register(r"study-logs", StudyLogViewSet, basename="study-log")
router.register(r"study-goals", StudyGoalViewSet, basename="study-goal")

urlpatterns = [
    path("public-badge/", PublicStudyBadgeView.as_view(), name="study-public-badge"),
    path("", include(router.urls)),
]
