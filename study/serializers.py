from rest_framework import serializers
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


class TopicSerializer(serializers.ModelSerializer):
    lab_count = serializers.IntegerField(source="labs.count", read_only=True)
    question_count = serializers.IntegerField(source="questions.count", read_only=True)
    certification_code = serializers.CharField(source="certification.code", read_only=True)

    class Meta:
        model = Topic
        fields = [
            "id",
            "certification",
            "certification_code",
            "domain_number",
            "domain_name",
            "domain_weight_pct",
            "name",
            "slug",
            "order",
            "description",
            "blueprint_ref",
            "icon",
            "lab_count",
            "question_count",
            "created_at",
            "updated_at",
        ]


class StudyCertificationSerializer(serializers.ModelSerializer):
    topics = TopicSerializer(many=True, read_only=True)
    total_topics = serializers.IntegerField(source="topics.count", read_only=True)
    total_questions = serializers.SerializerMethodField()
    total_labs = serializers.SerializerMethodField()

    class Meta:
        model = StudyCertification
        fields = [
            "id",
            "code",
            "name",
            "vendor",
            "exam_code",
            "description",
            "icon",
            "total_exam_time_minutes",
            "total_exam_questions",
            "passing_score_pct",
            "is_active",
            "total_topics",
            "total_questions",
            "total_labs",
            "topics",
            "created_at",
            "updated_at",
        ]

    def get_total_questions(self, obj):
        return Question.objects.filter(certification=obj).count()

    def get_total_labs(self, obj):
        return Lab.objects.filter(topic__certification=obj).count()


class LabSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source="topic.name", read_only=True)
    certification_code = serializers.CharField(source="topic.certification.code", read_only=True)
    user_attempt = serializers.SerializerMethodField()

    class Meta:
        model = Lab
        fields = [
            "id",
            "topic",
            "topic_name",
            "certification_code",
            "title",
            "slug",
            "difficulty",
            "estimated_time_minutes",
            "objectives",
            "topology_type",
            "topology_data",
            "prerequisites",
            "addressing_table",
            "step_by_step_tasks",
            "hints",
            "solution",
            "setup_template",
            "setup_template_type",
            "packet_tracer_file",
            "gns3_eve_file",
            "expected_config_rules",
            "aws_verification_checks",
            "teardown_instructions",
            "estimated_cost_usd",
            "free_tier_eligible",
            "order",
            "user_attempt",
            "created_at",
            "updated_at",
        ]

    def get_user_attempt(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            attempt = LabAttempt.objects.filter(user=request.user, lab=obj).first()
            if attempt:
                return {
                    "id": attempt.id,
                    "status": attempt.status,
                    "notes": attempt.notes,
                    "time_spent_seconds": attempt.time_spent_seconds,
                    "checker_results": attempt.checker_results,
                    "teardown_confirmed": attempt.teardown_confirmed,
                    "completed_at": attempt.completed_at,
                }
        return None


class LabAttemptSerializer(serializers.ModelSerializer):
    lab_title = serializers.CharField(source="lab.title", read_only=True)

    class Meta:
        model = LabAttempt
        fields = [
            "id",
            "user",
            "lab",
            "lab_title",
            "status",
            "notes",
            "time_spent_seconds",
            "submitted_config",
            "checker_results",
            "teardown_confirmed",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "created_at", "updated_at"]


class QuestionSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source="topic.name", read_only=True)
    certification_code = serializers.CharField(source="certification.code", read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "certification",
            "certification_code",
            "topic",
            "topic_name",
            "question_type",
            "text",
            "scenario_context",
            "code_output",
            "options",
            "correct_answers",
            "explanation",
            "distractor_notes",
            "trigger_words",
            "step_by_step_solution",
            "reference_doc_url",
            "difficulty",
            "tags",
            "source",
            "similarity_hash",
            "is_favorite",
            "is_reported",
            "report_reason",
            "created_at",
            "updated_at",
        ]


class ExamAnswerSerializer(serializers.ModelSerializer):
    question_details = QuestionSerializer(source="question", read_only=True)

    class Meta:
        model = ExamAnswer
        fields = [
            "id",
            "session",
            "question",
            "question_details",
            "user_answers",
            "is_correct",
            "flagged_for_review",
            "time_spent_seconds",
            "notes",
            "created_at",
        ]


class ExamSessionSerializer(serializers.ModelSerializer):
    answers = ExamAnswerSerializer(many=True, read_only=True)
    certification_code = serializers.CharField(source="certification.code", read_only=True)
    certification_name = serializers.CharField(source="certification.name", read_only=True)
    topic_name = serializers.CharField(source="topic.name", read_only=True)

    class Meta:
        model = ExamSession
        fields = [
            "id",
            "user",
            "certification",
            "certification_code",
            "certification_name",
            "mode",
            "topic",
            "topic_name",
            "total_questions",
            "duration_minutes",
            "time_spent_seconds",
            "score_pct",
            "passed",
            "domain_breakdown",
            "is_completed",
            "started_at",
            "completed_at",
            "answers",
        ]
        read_only_fields = ["user", "started_at"]


class FlashcardSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source="topic.name", read_only=True)
    certification_code = serializers.CharField(source="topic.certification.code", read_only=True)

    class Meta:
        model = Flashcard
        fields = [
            "id",
            "user",
            "topic",
            "topic_name",
            "certification_code",
            "question",
            "front",
            "back",
            "repetition_level",
            "interval_days",
            "ease_factor",
            "due_date",
            "last_reviewed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "created_at", "updated_at"]


class StudyNoteSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source="topic.name", read_only=True)

    class Meta:
        model = StudyNote
        fields = [
            "id",
            "user",
            "topic",
            "topic_name",
            "title",
            "content",
            "is_mistake_journal",
            "related_question",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "created_at", "updated_at"]


class InterviewBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewBrief
        fields = [
            "id",
            "organization",
            "company_summary",
            "tech_stack",
            "role_requirements_map",
            "technical_questions",
            "behavioral_star_questions",
            "questions_to_ask",
            "study_plan_30_60_90",
            "raw_input_text",
            "created_at",
            "updated_at",
        ]


class OrganizationSerializer(serializers.ModelSerializer):
    brief = InterviewBriefSerializer(read_only=True)
    linked_topic_details = TopicSerializer(source="linked_topics", many=True, read_only=True)
    mock_interviews_count = serializers.IntegerField(source="mock_interviews.count", read_only=True)
    latest_mock_score = serializers.SerializerMethodField()

    def get_latest_mock_score(self, obj):
        latest = obj.mock_interviews.filter(is_completed=True).order_by("-updated_at").first()
        return latest.overall_score if latest else None

    class Meta:
        model = Organization
        fields = [
            "id",
            "user",
            "company_name",
            "company_url",
            "job_posting_url",
            "role",
            "status",
            "application_date",
            "interview_date",
            "contacts",
            "notes",
            "linked_topics",
            "linked_topic_details",
            "brief",
            "mock_interviews_count",
            "latest_mock_score",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "created_at", "updated_at"]


class MockInterviewSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="organization.company_name", read_only=True)

    class Meta:
        model = MockInterview
        fields = [
            "id",
            "user",
            "organization",
            "company_name",
            "role_title",
            "transcript",
            "feedback",
            "overall_score",
            "is_completed",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "created_at", "updated_at"]


class StudyLogSerializer(serializers.ModelSerializer):
    certification_code = serializers.CharField(source="certification.code", read_only=True)
    topic_name = serializers.CharField(source="topic.name", read_only=True)

    class Meta:
        model = StudyLog
        fields = [
            "id",
            "user",
            "certification",
            "certification_code",
            "topic",
            "topic_name",
            "session_type",
            "duration_minutes",
            "date",
            "notes",
            "created_at",
        ]
        read_only_fields = ["user", "created_at"]


class StudyGoalSerializer(serializers.ModelSerializer):
    certification_code = serializers.CharField(source="certification.code", read_only=True)

    class Meta:
        model = StudyGoal
        fields = [
            "id",
            "user",
            "certification",
            "certification_code",
            "target_exam_date",
            "daily_goal_minutes",
            "weekly_goal_days",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "created_at", "updated_at"]
