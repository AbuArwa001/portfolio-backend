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
from .ai_service import generate_questions_with_claude


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

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Calls Claude API server-side to generate N questions for a topic."""
        topic_id = request.data.get("topic_id")
        if not topic_id:
            return Response({"error": "topic_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        topic = get_object_or_404(Topic, id=topic_id)
        count = min(int(request.data.get("count", 10)), 25)
        difficulty = request.data.get("difficulty", "medium")

        created_questions, message = generate_questions_with_claude(topic, count=count, difficulty=difficulty)
        serializer = QuestionSerializer(created_questions, many=True)
        return Response({
            "message": message,
            "created_count": len(created_questions),
            "questions": serializer.data
        })

    @action(detail=False, methods=["get"])
    def retry_queue(self, request):
        """Returns questions previously answered incorrectly by the user that are queued for retry."""
        cert_code = request.query_params.get("cert")
        wrong_q_ids = ExamAnswer.objects.filter(
            session__user=request.user,
            is_correct=False
        ).values_list("question_id", flat=True).distinct()

        # Filter out questions that have since been answered correctly
        correct_q_ids = ExamAnswer.objects.filter(
            session__user=request.user,
            is_correct=True
        ).values_list("question_id", flat=True).distinct()

        active_wrong_ids = set(wrong_q_ids) - set(correct_q_ids)
        qs = Question.objects.filter(id__in=active_wrong_ids).select_related("certification", "topic")
        if cert_code:
            qs = qs.filter(certification__code__iexact=cert_code)

        return Response(QuestionSerializer(qs, many=True).data)


class ExamSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ExamSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ExamSession.objects.filter(user=self.request.user).select_related(
            "certification", "topic"
        ).prefetch_related("answers", "answers__question")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["post"])
    def start(self, request):
        """Initializes a new exam session (practice, timed_mock, retry_wrong, or weak_drill)."""
        import random
        cert_code = request.data.get("certification_code", "CCNA-200-301")
        cert = get_object_or_404(StudyCertification, code__iexact=cert_code)
        mode = request.data.get("mode", "practice")
        topic_id = request.data.get("topic_id")
        requested_count = int(request.data.get("question_count", 0))

        topic = None
        if topic_id:
            topic = get_object_or_404(Topic, id=topic_id, certification=cert)

        question_pool = []
        duration = 120 if "CCNA" in cert.code else 130

        if mode == "practice":
            if not topic:
                topic = cert.topics.first()
            qs = Question.objects.filter(topic=topic)
            if qs.count() < (requested_count or 10):
                need = max(5, (requested_count or 10) - qs.count())
                generate_questions_with_claude(topic, count=need)
                qs = Question.objects.filter(topic=topic)
            target_count = requested_count or 10
            question_pool = list(qs.order_by("?")[:target_count])
            duration = target_count * 2

        elif mode == "timed_mock":
            target_count = requested_count or (100 if "CCNA" in cert.code else 65)
            all_topics = list(cert.topics.all())
            collected = []
            for t in all_topics:
                t_qs = list(Question.objects.filter(topic=t))
                if not t_qs:
                    new_qs, _ = generate_questions_with_claude(t, count=3)
                    collected.extend(new_qs)
                else:
                    collected.extend(t_qs[:4])

            random.shuffle(collected)
            question_pool = collected[:target_count]
            if len(question_pool) < target_count and all_topics:
                more_needed = target_count - len(question_pool)
                for t in all_topics[:more_needed]:
                    new_qs, _ = generate_questions_with_claude(t, count=2)
                    question_pool.extend(new_qs)
                    if len(question_pool) >= target_count:
                        break
            question_pool = question_pool[:target_count]

        elif mode == "retry_wrong":
            wrong_q_ids = ExamAnswer.objects.filter(
                session__user=request.user,
                session__certification=cert,
                is_correct=False
            ).values_list("question_id", flat=True).distinct()
            correct_q_ids = ExamAnswer.objects.filter(
                session__user=request.user,
                session__certification=cert,
                is_correct=True
            ).values_list("question_id", flat=True).distinct()
            active_wrong = set(wrong_q_ids) - set(correct_q_ids)
            qs = Question.objects.filter(id__in=active_wrong)
            if not qs.exists():
                qs = Question.objects.filter(certification=cert)
            question_pool = list(qs.order_by("?")[:(requested_count or 15)])
            duration = max(10, len(question_pool) * 2)

        elif mode == "weak_drill":
            topic_stats = Topic.objects.filter(certification=cert).annotate(
                total_answered=Count("questions__exam_answers", filter=Q(questions__exam_answers__session__user=request.user)),
                correct_count=Count("questions__exam_answers", filter=Q(questions__exam_answers__session__user=request.user, questions__exam_answers__is_correct=True))
            )
            weak_topics = sorted(topic_stats, key=lambda t: (t.correct_count / t.total_answered if t.total_answered > 0 else 0))
            drill_topics = weak_topics[:3] if weak_topics else list(cert.topics.all()[:3])
            collected = []
            for t in drill_topics:
                t_qs = list(Question.objects.filter(topic=t))
                if len(t_qs) < 5:
                    new_qs, _ = generate_questions_with_claude(t, count=5)
                    collected.extend(new_qs)
                else:
                    collected.extend(t_qs[:5])
            random.shuffle(collected)
            question_pool = collected[:(requested_count or 15)]
            duration = max(10, len(question_pool) * 2)

        session = ExamSession.objects.create(
            user=request.user,
            certification=cert,
            mode=mode,
            topic=topic,
            total_questions=len(question_pool),
            duration_minutes=duration,
        )

        return Response({
            "session_id": session.id,
            "certification_code": cert.code,
            "certification_name": cert.name,
            "mode": mode,
            "topic_name": topic.name if topic else None,
            "total_questions": session.total_questions,
            "duration_minutes": session.duration_minutes,
            "questions": QuestionSerializer(question_pool, many=True).data,
            "started_at": session.started_at.isoformat(),
        })

    @action(detail=True, methods=["post"])
    def submit_answer(self, request, pk=None):
        """Submits an answer for a question in this session and returns instant evaluation."""
        session = self.get_object()
        question_id = request.data.get("question_id")
        user_answers = request.data.get("user_answers", [])
        time_spent = int(request.data.get("time_spent_seconds", 0))
        flagged = bool(request.data.get("flagged_for_review", False))

        question = get_object_or_404(Question, id=question_id)

        # Check correctness
        normalized_user = set(str(a).strip().upper() for a in user_answers)
        normalized_correct = set(str(a).strip().upper() for a in question.correct_answers)
        is_correct = (normalized_user == normalized_correct) and len(normalized_correct) > 0

        answer, _ = ExamAnswer.objects.update_or_create(
            session=session,
            question=question,
            defaults={
                "user_answers": user_answers,
                "is_correct": is_correct,
                "time_spent_seconds": time_spent,
                "flagged_for_review": flagged,
            }
        )

        # If wrong, automatically ensure an SM-2 spaced repetition card exists
        if not is_correct:
            Flashcard.objects.get_or_create(
                user=request.user,
                topic=question.topic,
                question=question,
                defaults={
                    "front": f"[{question.topic.name}] {question.text[:300]}",
                    "back": f"Correct Answer: {', '.join(question.correct_answers)}\n\n{question.explanation}\n\nKey Concept: {question.trigger_words}",
                    "due_date": timezone.now().date(),
                }
            )

        return Response({
            "answer_id": answer.id,
            "question_id": question.id,
            "is_correct": is_correct,
            "user_answers": user_answers,
            "correct_answers": question.correct_answers,
            "explanation": question.explanation,
            "distractor_notes": question.distractor_notes,
            "trigger_words": question.trigger_words,
            "step_by_step_solution": question.step_by_step_solution,
            "reference_doc_url": question.reference_doc_url,
        })

    @action(detail=True, methods=["post"])
    def finish(self, request, pk=None):
        """Finalizes the exam session, calculates scores and domain breakdowns, and logs study activity."""
        session = self.get_object()
        answers = session.answers.select_related("question", "question__topic")
        total_answers = answers.count()
        correct_count = answers.filter(is_correct=True).count()

        total_q = session.total_questions or total_answers or 1
        score_pct = round((correct_count / total_q) * 100, 1)

        pass_threshold = session.certification.passing_score_pct or 80
        passed = score_pct >= pass_threshold

        domain_breakdown = {}
        for ans in answers:
            d_name = ans.question.topic.domain_name or f"Domain {ans.question.topic.domain_number}"
            if d_name not in domain_breakdown:
                domain_breakdown[d_name] = {"total": 0, "correct": 0, "pct": 0}
            domain_breakdown[d_name]["total"] += 1
            if ans.is_correct:
                domain_breakdown[d_name]["correct"] += 1

        for d_name, stat in domain_breakdown.items():
            stat["pct"] = round((stat["correct"] / stat["total"] * 100), 1) if stat["total"] > 0 else 0

        total_time = sum(answers.values_list("time_spent_seconds", flat=True)) or session.time_spent_seconds

        session.score_pct = score_pct
        session.passed = passed
        session.time_spent_seconds = total_time
        session.domain_breakdown = domain_breakdown
        session.is_completed = True
        session.completed_at = timezone.now()
        session.save()

        minutes_spent = max(5, round(total_time / 60))
        StudyLog.objects.create(
            user=request.user,
            certification=session.certification,
            topic=session.topic,
            session_type="exam" if session.mode == "timed_mock" else "quiz",
            duration_minutes=minutes_spent,
            date=timezone.now().date(),
            notes=f"{session.mode.title()} session for {session.certification.code}. Score: {score_pct}%. ({correct_count}/{total_q} correct)"
        )

        return Response(ExamSessionSerializer(session).data)

    @action(detail=True, methods=["get"])
    def review(self, request, pk=None):
        """Returns complete end-of-test review details: answers vs correct, explanations, trigger words, and doc links."""
        session = self.get_object()
        answers = session.answers.select_related("question", "question__topic").all()

        wrong_answers = []
        all_answers = []

        for ans in answers:
            q = ans.question
            item = {
                "question_id": q.id,
                "question_text": q.text,
                "scenario_context": q.scenario_context,
                "code_output": q.code_output,
                "question_type": q.question_type,
                "options": q.options,
                "user_answers": ans.user_answers,
                "correct_answers": q.correct_answers,
                "is_correct": ans.is_correct,
                "flagged_for_review": ans.flagged_for_review,
                "time_spent_seconds": ans.time_spent_seconds,
                "explanation": q.explanation,
                "distractor_notes": q.distractor_notes,
                "trigger_words": q.trigger_words,
                "step_by_step_solution": q.step_by_step_solution,
                "reference_doc_url": q.reference_doc_url,
                "domain_number": q.topic.domain_number,
                "domain_name": q.topic.domain_name,
                "topic_name": q.topic.name,
                "difficulty": q.difficulty,
            }
            all_answers.append(item)
            if not ans.is_correct:
                wrong_answers.append(item)

        return Response({
            "session": ExamSessionSerializer(session).data,
            "total_questions": session.total_questions,
            "correct_count": len(all_answers) - len(wrong_answers),
            "wrong_count": len(wrong_answers),
            "score_pct": float(session.score_pct),
            "passed": session.passed,
            "domain_breakdown": session.domain_breakdown,
            "wrong_questions": wrong_answers,
            "all_questions": all_answers,
        })


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
