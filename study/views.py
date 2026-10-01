from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Q, Avg
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

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
from .serializers import (
    StudyCertificationSerializer,
    TopicSerializer,
    LabSerializer,
    LabAttemptSerializer,
    QuestionSerializer,
    ExamSessionSerializer,
    ExamAnswerSerializer,
    FlashcardSerializer,
    StudyNoteSerializer,
    OrganizationSerializer,
    InterviewBriefSerializer,
    MockInterviewSerializer,
    StudyLogSerializer,
    StudyGoalSerializer,
)


class StudyCertificationViewSet(viewsets.ModelViewSet):
    queryset = StudyCertification.objects.filter(is_active=True).prefetch_related("topics")
    serializer_class = StudyCertificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["get"])
    def progress(self, request, pk=None):
        """Returns consolidated learning progress, accuracy, labs, and readiness score for this certification."""
        cert = self.get_object()
        user = request.user

        total_topics = cert.topics.count()
        total_labs = Lab.objects.filter(topic__certification=cert).count()
        completed_labs = LabAttempt.objects.filter(
            user=user,
            lab__topic__certification=cert,
            status="completed"
        ).count()

        # Questions & accuracy stats
        answers = ExamAnswer.objects.filter(
            session__user=user,
            session__certification=cert
        )
        total_answered = answers.count()
        correct_answers = answers.filter(is_correct=True).count()
        accuracy_pct = round((correct_answers / total_answered * 100), 1) if total_answered > 0 else 0

        # Exam readiness formula based on lab completion, question bank volume, and mock exam average
        mock_sessions = ExamSession.objects.filter(
            user=user,
            certification=cert,
            mode="timed_mock",
            is_completed=True
        )
        mock_avg = mock_sessions.aggregate(avg=Avg("score_pct"))["avg"] or 0
        readiness_score = round(
            (0.35 * (completed_labs / total_labs * 100 if total_labs > 0 else 0)) +
            (0.35 * accuracy_pct) +
            (0.30 * float(mock_avg)),
            1
        )

        return Response({
            "certification": cert.code,
            "name": cert.name,
            "total_topics": total_topics,
            "total_labs": total_labs,
            "completed_labs": completed_labs,
            "lab_completion_pct": round((completed_labs / total_labs * 100), 1) if total_labs > 0 else 0,
            "total_questions_attempted": total_answered,
            "accuracy_pct": accuracy_pct,
            "mock_exams_taken": mock_sessions.count(),
            "mock_exam_average": round(float(mock_avg), 1),
            "readiness_score": min(100.0, readiness_score),
        })


class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.all().select_related("certification")
    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        cert_code = self.request.query_params.get("cert")
        domain = self.request.query_params.get("domain")
        if cert_code:
            qs = qs.filter(certification__code__iexact=cert_code)
        if domain:
            qs = qs.filter(domain_number=domain)
        return qs


class LabViewSet(viewsets.ModelViewSet):
    queryset = Lab.objects.all().select_related("topic", "topic__certification")
    serializer_class = LabSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        cert_code = self.request.query_params.get("cert")
        topic_id = self.request.query_params.get("topic")
        difficulty = self.request.query_params.get("difficulty")
        if cert_code:
            qs = qs.filter(topic__certification__code__iexact=cert_code)
        if topic_id:
            qs = qs.filter(topic_id=topic_id)
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        return qs


class LabAttemptViewSet(viewsets.ModelViewSet):
    serializer_class = LabAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LabAttempt.objects.filter(user=self.request.user).select_related("lab")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all().select_related("certification", "topic")
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        cert_code = self.request.query_params.get("cert")
        topic_id = self.request.query_params.get("topic")
        q_type = self.request.query_params.get("type")
        difficulty = self.request.query_params.get("difficulty")
        favorites = self.request.query_params.get("favorites")

        if cert_code:
            qs = qs.filter(certification__code__iexact=cert_code)
        if topic_id:
            qs = qs.filter(topic_id=topic_id)
        if q_type:
            qs = qs.filter(question_type=q_type)
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        if favorites == "true":
            qs = qs.filter(is_favorite=True)
        return qs

    @action(detail=True, methods=["post"])
    def toggle_favorite(self, request, pk=None):
        question = self.get_object()
        question.is_favorite = not question.is_favorite
        question.save(update_fields=["is_favorite"])
        return Response({"is_favorite": question.is_favorite})

    @action(detail=True, methods=["post"])
    def report_issue(self, request, pk=None):
        question = self.get_object()
        reason = request.data.get("reason", "")
        question.is_reported = True
        question.report_reason = reason
        question.save(update_fields=["is_reported", "report_reason"])
        return Response({"status": "reported", "message": "Thank you for the report"})


class ExamSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ExamSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ExamSession.objects.filter(user=self.request.user).select_related(
            "certification", "topic"
        ).prefetch_related("answers", "answers__question")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExamAnswerViewSet(viewsets.ModelViewSet):
    serializer_class = ExamAnswerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ExamAnswer.objects.filter(session__user=self.request.user).select_related("question")


class FlashcardViewSet(viewsets.ModelViewSet):
    serializer_class = FlashcardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Flashcard.objects.filter(user=self.request.user).select_related("topic", "topic__certification")
        cert_code = self.request.query_params.get("cert")
        topic_id = self.request.query_params.get("topic")
        due_only = self.request.query_params.get("due")

        if cert_code:
            qs = qs.filter(topic__certification__code__iexact=cert_code)
        if topic_id:
            qs = qs.filter(topic_id=topic_id)
        if due_only == "true":
            qs = qs.filter(due_date__lte=timezone.now().date())
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        """SM-2 Spaced Repetition Review calculation.
        Rating quality from 0 (complete blackout) to 5 (perfect recall).
        """
        flashcard = self.get_object()
        try:
            quality = int(request.data.get("quality", 4))
        except (ValueError, TypeError):
            quality = 4

        # SM-2 Algorithm implementation
        if quality < 3:
            flashcard.repetition_level = 0
            flashcard.interval_days = 1
        else:
            if flashcard.repetition_level == 0:
                flashcard.interval_days = 1
            elif flashcard.repetition_level == 1:
                flashcard.interval_days = 6
            else:
                flashcard.interval_days = int(round(flashcard.interval_days * float(flashcard.ease_factor)))
            flashcard.repetition_level += 1

        new_ef = float(flashcard.ease_factor) + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        flashcard.ease_factor = max(1.30, round(new_ef, 2))
        flashcard.due_date = timezone.now().date() + timezone.timedelta(days=flashcard.interval_days)
        flashcard.last_reviewed_at = timezone.now()
        flashcard.save()

        return Response(FlashcardSerializer(flashcard).data)


class StudyNoteViewSet(viewsets.ModelViewSet):
    serializer_class = StudyNoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = StudyNote.objects.filter(user=self.request.user).select_related("topic")
        mistakes_only = self.request.query_params.get("mistakes")
        topic_id = self.request.query_params.get("topic")
        if mistakes_only == "true":
            qs = qs.filter(is_mistake_journal=True)
        if topic_id:
            qs = qs.filter(topic_id=topic_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Organization.objects.filter(user=self.request.user).prefetch_related("linked_topics")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class InterviewBriefViewSet(viewsets.ModelViewSet):
    serializer_class = InterviewBriefSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InterviewBrief.objects.filter(organization__user=self.request.user)


class MockInterviewViewSet(viewsets.ModelViewSet):
    serializer_class = MockInterviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MockInterview.objects.filter(user=self.request.user).select_related("organization")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class StudyLogViewSet(viewsets.ModelViewSet):
    serializer_class = StudyLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return StudyLog.objects.filter(user=self.request.user).select_related("certification", "topic")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class StudyGoalViewSet(viewsets.ModelViewSet):
    serializer_class = StudyGoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return StudyGoal.objects.filter(user=self.request.user).select_related("certification")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PublicStudyBadgeView(APIView):
    """Public read-only progress badge endpoint.
    Exposes only high-level certification progress %, current streak, and total study hours.
    No private notes, questions, organizations, or credentials are exposed.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        certifications = StudyCertification.objects.filter(is_active=True)
        badges = []

        for cert in certifications:
            total_labs = Lab.objects.filter(topic__certification=cert).count()
            completed_labs = LabAttempt.objects.filter(
                lab__topic__certification=cert,
                status="completed"
            ).count()

            # Questions answered
            total_questions = cert.questions.count()
            answers = ExamAnswer.objects.filter(session__certification=cert, is_correct=True).count()

            lab_score = (completed_labs / total_labs * 100) if total_labs > 0 else 0
            question_score = (min(100.0, answers / (cert.total_exam_questions or 100) * 100))
            overall_progress = round((lab_score * 0.5) + (question_score * 0.5))

            badges.append({
                "code": cert.code,
                "name": cert.name,
                "vendor": cert.vendor,
                "exam_code": cert.exam_code,
                "progress_pct": min(100, overall_progress),
                "status": "In Progress" if overall_progress < 100 else "Completed",
            })

        # Calculate study streak from StudyLog
        today = timezone.now().date()
        recent_logs = StudyLog.objects.values_list("date", flat=True).distinct().order_by("-date")[:30]
        recent_dates = set(recent_logs)

        streak = 0
        cur_date = today
        while cur_date in recent_dates or (streak == 0 and (cur_date - timezone.timedelta(days=1)) in recent_dates):
            if cur_date in recent_dates:
                streak += 1
            cur_date -= timezone.timedelta(days=1)

        total_study_minutes = sum(StudyLog.objects.values_list("duration_minutes", flat=True))
        total_hours = round(total_study_minutes / 60, 1)

        return Response({
            "certifications": badges,
            "streak_days": streak,
            "total_study_hours": total_hours,
            "last_updated": timezone.now().isoformat(),
        })
