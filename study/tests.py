from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import StudyCertification, Topic, Lab, Question

User = get_user_model()


class StudyPlatformTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testadmin",
            email="testadmin@example.com",
            password="testpassword123",
            is_staff=True
        )

        self.ccna = StudyCertification.objects.create(
            code="CCNA-200-301",
            name="Cisco Certified Network Associate",
            vendor="Cisco",
            exam_code="200-301",
            total_exam_time_minutes=120,
            total_exam_questions=100
        )

        self.topic = Topic.objects.create(
            certification=self.ccna,
            domain_number=2,
            domain_name="Network Access",
            domain_weight_pct=20,
            name="VLANs & Segmentation",
            slug="2-1-vlans-segmentation",
            blueprint_ref="2.1"
        )

        self.lab = Lab.objects.create(
            topic=self.topic,
            title="Configuring VLANs and Trunks",
            slug="configuring-vlans-trunks",
            difficulty="beginner",
            estimated_time_minutes=30
        )

    def test_certification_and_topic_str(self):
        self.assertIn("CCNA-200-301", str(self.ccna))
        self.assertIn("VLANs & Segmentation", str(self.topic))

    def test_public_study_badge_endpoint(self):
        """Public endpoint should allow unauthenticated access and return safe badge statistics."""
        response = self.client.get("/api/v1/study/public-badge/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("certifications", data)
        self.assertIn("streak_days", data)
        self.assertIn("total_study_hours", data)
        self.assertTrue(len(data["certifications"]) >= 1)
        self.assertEqual(data["certifications"][0]["code"], "CCNA-200-301")

    def test_unauthenticated_api_endpoints_denied(self):
        """Study topics, labs, and question banks must sit strictly behind admin authentication."""
        response = self.client.get("/api/v1/study/topics/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.get("/api/v1/study/labs/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_admin_access(self):
        """Authenticated admin user can access study topics and labs."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/study/topics/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get("/api/v1/study/labs/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
