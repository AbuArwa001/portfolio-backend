from django.db import models
from django.conf import settings
from django.utils import timezone


class StudyCertification(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=50, unique=True, help_text="e.g. CCNA-200-301, AWS-SAA-C03")
    name = models.CharField(max_length=255)
    vendor = models.CharField(max_length=100, default="Cisco")  # Cisco, AWS, etc.
    exam_code = models.CharField(max_length=50, default="200-301")
    description = models.TextField(blank=True, default="")
    icon = models.CharField(max_length=50, default="Network", help_text="Lucide icon name or identifier")
    total_exam_time_minutes = models.IntegerField(default=120)
    total_exam_questions = models.IntegerField(default=100)
    passing_score_pct = models.IntegerField(default=82)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "Study Certification"
        verbose_name_plural = "Study Certifications"

    def __str__(self):
        return f"{self.name} ({self.code})"


class Topic(models.Model):
    id = models.AutoField(primary_key=True)
    certification = models.ForeignKey(
        StudyCertification,
        on_delete=models.CASCADE,
        related_name="topics"
    )
    domain_number = models.IntegerField(default=1)
    domain_name = models.CharField(max_length=255, default="General")
    domain_weight_pct = models.IntegerField(default=0, help_text="Official exam blueprint domain percentage")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    order = models.IntegerField(default=0)
    description = models.TextField(blank=True, default="")
    blueprint_ref = models.CharField(max_length=50, blank=True, default="", help_text="e.g. 1.1, 2.3")
    icon = models.CharField(max_length=50, blank=True, default="BookOpen")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["certification", "domain_number", "order", "name"]
        unique_together = [["certification", "slug"]]
        verbose_name = "Topic"
        verbose_name_plural = "Topics"

    def __str__(self):
        return f"[{self.certification.code}] {self.domain_number}.{self.order} {self.name}"


class Lab(models.Model):
    DIFFICULTY_CHOICES = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]
    TOPOLOGY_TYPE_CHOICES = [
        ("svg", "SVG Diagram"),
        ("image", "Image URL"),
    ]
    SETUP_TEMPLATE_CHOICES = [
        ("cisco_initial", "Cisco Initial Config"),
        ("cloudformation", "CloudFormation"),
        ("terraform", "Terraform"),
        ("none", "None"),
    ]

    id = models.AutoField(primary_key=True)
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="labs"
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default="intermediate")
    estimated_time_minutes = models.IntegerField(default=45)
    objectives = models.JSONField(default=list, blank=True, help_text="List of learning objectives")
    
    # Topology & Architecture Diagram
    topology_type = models.CharField(max_length=20, choices=TOPOLOGY_TYPE_CHOICES, default="svg")
    topology_data = models.TextField(blank=True, default="", help_text="Raw SVG content or image URL")
    
    prerequisites = models.TextField(blank=True, default="")
    addressing_table = models.JSONField(
        default=list,
        blank=True,
        help_text="Addressing table entries: [{device, interface, ip, subnet, default_gateway}]"
    )
    step_by_step_tasks = models.JSONField(
        default=list,
        blank=True,
        help_text="Task list: [{step_num, title, instructions, verify_prompt}]"
    )
    hints = models.JSONField(default=list, blank=True, help_text="Collapsible hints: [string]")
    solution = models.TextField(blank=True, default="", help_text="Full solution CLI commands or architecture walkthrough")
    
    # Setup & Downloadable files
    setup_template = models.TextField(blank=True, default="", help_text="CFN/Terraform template or Cisco startup config")
    setup_template_type = models.CharField(max_length=30, choices=SETUP_TEMPLATE_CHOICES, default="none")
    packet_tracer_file = models.FileField(upload_to="study/labs/pkt/", blank=True, null=True)
    gns3_eve_file = models.FileField(upload_to="study/labs/gns3/", blank=True, null=True)
    
    # Config Grading & Verification
    expected_config_rules = models.JSONField(
        default=list,
        blank=True,
        help_text="Config checker rules: [{pattern: regex, description: string, section: string, required: bool}]"
    )
    aws_verification_checks = models.JSONField(
        default=list,
        blank=True,
        help_text="Read-only AWS SDK verification checks: [{service, check_type, resource_name, params, expected}]"
    )
    teardown_instructions = models.TextField(blank=True, default="", help_text="Mandatory cleanup checklist & steps")
    estimated_cost_usd = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    free_tier_eligible = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["topic", "order", "title"]
        unique_together = [["topic", "slug"]]
        verbose_name = "Lab"
        verbose_name_plural = "Labs"

    def __str__(self):
        return f"{self.title} ({self.topic.name})"


class LabAttempt(models.Model):
    STATUS_CHOICES = [
        ("not_started", "Not Started"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lab_attempts"
    )
    lab = models.ForeignKey(
        Lab,
        on_delete=models.CASCADE,
        related_name="attempts"
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="not_started")
    notes = models.TextField(blank=True, default="")
    time_spent_seconds = models.IntegerField(default=0)
    submitted_config = models.TextField(blank=True, default="")
    checker_results = models.JSONField(default=dict, blank=True, help_text="Grading results: passed_rules, missing_rules, score")
    teardown_confirmed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        unique_together = [["user", "lab"]]
        verbose_name = "Lab Attempt"
        verbose_name_plural = "Lab Attempts"

    def __str__(self):
        return f"{self.user} - {self.lab.title} ({self.status})"


class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ("single_choice", "Single Choice"),
        ("multi_select", "Multiple Select"),
        ("scenario_output", "Scenario with Output Interpretation"),
        ("drag_and_drop", "Drag and Drop / Ordering"),
        ("subnetting_calc", "Subnetting Calculation"),
    ]
    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]
    SOURCE_CHOICES = [
        ("ai", "Claude AI Generated"),
        ("manual", "Manual Entry"),
    ]

    id = models.AutoField(primary_key=True)
    certification = models.ForeignKey(
        StudyCertification,
        on_delete=models.CASCADE,
        related_name="questions"
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="questions"
    )
    question_type = models.CharField(max_length=30, choices=QUESTION_TYPE_CHOICES, default="single_choice")
    text = models.TextField(help_text="The question prompt")
    scenario_context = models.TextField(blank=True, default="", help_text="Narrative scenario context if applicable")
    code_output = models.TextField(blank=True, default="", help_text="CLI or JSON output to interpret")
    options = models.JSONField(default=list, help_text="List of choices: [{id: 'A', text: '...'}, {id: 'B', text: '...'}]")
    correct_answers = models.JSONField(default=list, help_text="Correct option IDs, e.g. ['A'] or ['B', 'D']")
    explanation = models.TextField(help_text="Why the correct answer is right")
    distractor_notes = models.JSONField(default=dict, blank=True, help_text="Why each wrong option is incorrect: {'B': '...', 'C': '...'}")
    trigger_words = models.TextField(blank=True, default="", help_text="Key trigger phrases/concepts to spot next time")
    step_by_step_solution = models.TextField(blank=True, default="", help_text="Step-by-step resolution path")
    reference_doc_url = models.URLField(max_length=500, blank=True, default="", help_text="Link to relevant Cisco or AWS documentation")
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default="medium")
    tags = models.JSONField(default=list, blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="ai")
    similarity_hash = models.CharField(max_length=64, blank=True, db_index=True)
    is_favorite = models.BooleanField(default=False)
    is_reported = models.BooleanField(default=False)
    report_reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Question"
        verbose_name_plural = "Questions"

    def __str__(self):
        return f"[{self.topic.name}] {self.text[:60]}..."


class ExamSession(models.Model):
    MODE_CHOICES = [
        ("practice", "Topic Practice (Instant Feedback)"),
        ("timed_mock", "Timed Mock Exam"),
        ("retry_wrong", "Retry Wrong Answers"),
        ("weak_drill", "Weak-Area Drilling"),
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="exam_sessions"
    )
    certification = models.ForeignKey(
        StudyCertification,
        on_delete=models.CASCADE,
        related_name="exam_sessions"
    )
    mode = models.CharField(max_length=30, choices=MODE_CHOICES, default="practice")
    topic = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="practice_sessions"
    )
    total_questions = models.IntegerField(default=0)
    duration_minutes = models.IntegerField(default=120)
    time_spent_seconds = models.IntegerField(default=0)
    score_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    passed = models.BooleanField(default=False)
    domain_breakdown = models.JSONField(default=dict, blank=True, help_text="Breakdown per domain: {domain_name: {total, correct, pct}}")
    is_completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "Exam Session"
        verbose_name_plural = "Exam Sessions"

    def __str__(self):
        return f"{self.user} - {self.certification.code} {self.mode} ({self.score_pct}%)"


class ExamAnswer(models.Model):
    id = models.AutoField(primary_key=True)
    session = models.ForeignKey(
        ExamSession,
        on_delete=models.CASCADE,
        related_name="answers"
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="exam_answers"
    )
    user_answers = models.JSONField(default=list, help_text="List of selected option IDs, e.g. ['A']")
    is_correct = models.BooleanField(default=False)
    flagged_for_review = models.BooleanField(default=False)
    time_spent_seconds = models.IntegerField(default=0)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        unique_together = [["session", "question"]]
        verbose_name = "Exam Answer"
        verbose_name_plural = "Exam Answers"

    def __str__(self):
        return f"Session #{self.session.id} - Q#{self.question.id} ({'Correct' if self.is_correct else 'Wrong'})"


class Flashcard(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="flashcards"
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="flashcards"
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="flashcards"
    )
    front = models.TextField(help_text="Prompt or question")
    back = models.TextField(help_text="Answer and detailed explanation")
    
    # SM-2 Spaced Repetition Parameters
    repetition_level = models.IntegerField(default=0)
    interval_days = models.IntegerField(default=1)
    ease_factor = models.DecimalField(max_digits=4, decimal_places=2, default=2.50)
    due_date = models.DateField(default=timezone.now)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_date"]
        verbose_name = "Flashcard"
        verbose_name_plural = "Flashcards"

    def __str__(self):
        return f"Flashcard #{self.id} ({self.topic.name}): {self.front[:50]}..."


class StudyNote(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_notes"
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="notes"
    )
    title = models.CharField(max_length=255)
    content = models.TextField(help_text="Markdown formatted notes")
    is_mistake_journal = models.BooleanField(default=False, help_text="Mark if this is an entry in the personal mistakes journal")
    related_question = models.ForeignKey(
        Question,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Study Note"
        verbose_name_plural = "Study Notes"

    def __str__(self):
        return f"[{'Mistake Journal' if self.is_mistake_journal else 'Note'}] {self.title}"


class Organization(models.Model):
    STATUS_CHOICES = [
        ("Wishlist", "Wishlist"),
        ("Applied", "Applied"),
        ("Interviewing", "Interviewing"),
        ("Offer", "Offer"),
        ("Rejected", "Rejected"),
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="interview_organizations"
    )
    company_name = models.CharField(max_length=255)
    company_url = models.URLField(max_length=500, blank=True, default="")
    job_posting_url = models.URLField(max_length=1000, blank=True, default="")
    role = models.CharField(max_length=255)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="Wishlist")
    application_date = models.DateField(null=True, blank=True)
    interview_date = models.DateTimeField(null=True, blank=True)
    contacts = models.JSONField(default=list, blank=True, help_text="[{name, role, email, linkedin}]")
    notes = models.TextField(blank=True, default="")
    linked_topics = models.ManyToManyField(
        Topic,
        blank=True,
        related_name="linked_organizations",
        help_text="Topics required or valued by this role (e.g. OSPF, VPC, S3)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"

    def __str__(self):
        return f"{self.company_name} - {self.role} ({self.status})"


class InterviewBrief(models.Model):
    id = models.AutoField(primary_key=True)
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name="brief"
    )
    company_summary = models.TextField(blank=True, default="")
    tech_stack = models.JSONField(default=list, blank=True)
    role_requirements_map = models.JSONField(
        default=list,
        blank=True,
        help_text="Job requirements mapped to user skills and portfolio projects"
    )
    technical_questions = models.JSONField(default=list, blank=True)
    behavioral_star_questions = models.JSONField(
        default=list,
        blank=True,
        help_text="Target behavioral questions with STAR outlines"
    )
    questions_to_ask = models.JSONField(default=list, blank=True)
    study_plan_30_60_90 = models.JSONField(
        default=dict,
        blank=True,
        help_text="30, 60, 90 day study plans mapped to CCNA and AWS topics"
    )
    raw_input_text = models.TextField(blank=True, default="", help_text="Scraped or pasted JD / company details")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Interview Brief"
        verbose_name_plural = "Interview Briefs"

    def __str__(self):
        return f"Brief for {self.organization.company_name} ({self.organization.role})"


class MockInterview(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mock_interviews"
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="mock_interviews"
    )
    role_title = models.CharField(max_length=255)
    transcript = models.JSONField(
        default=list,
        help_text="Transcript: [{role: 'interviewer'|'candidate', content: '...', timestamp: '...'}]"
    )
    feedback = models.JSONField(
        default=dict,
        blank=True,
        help_text="Scoring, strengths, weaknesses, tips"
    )
    overall_score = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Mock Interview"
        verbose_name_plural = "Mock Interviews"

    def __str__(self):
        return f"Mock Interview with {self.organization.company_name} - Score: {self.overall_score}/100"


class StudyLog(models.Model):
    SESSION_TYPE_CHOICES = [
        ("lab", "Lab Session"),
        ("quiz", "Topic Practice"),
        ("exam", "Mock Exam"),
        ("flashcard", "Flashcard Review"),
        ("reading", "Reading & Notes"),
        ("interview_prep", "Interview Prep"),
        ("pomodoro", "Pomodoro Study Session"),
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_logs"
    )
    certification = models.ForeignKey(
        StudyCertification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="study_logs"
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="study_logs"
    )
    session_type = models.CharField(max_length=30, choices=SESSION_TYPE_CHOICES, default="quiz")
    duration_minutes = models.IntegerField(default=25)
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name = "Study Log"
        verbose_name_plural = "Study Logs"

    def __str__(self):
        return f"{self.user} - {self.session_type} ({self.duration_minutes} min on {self.date})"


class StudyGoal(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_goals"
    )
    certification = models.ForeignKey(
        StudyCertification,
        on_delete=models.CASCADE,
        related_name="goals"
    )
    target_exam_date = models.DateField()
    daily_goal_minutes = models.IntegerField(default=60)
    weekly_goal_days = models.IntegerField(default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["target_exam_date"]
        unique_together = [["user", "certification"]]
        verbose_name = "Study Goal"
        verbose_name_plural = "Study Goals"

    def __str__(self):
        return f"{self.user} target for {self.certification.code}: {self.target_exam_date}"
