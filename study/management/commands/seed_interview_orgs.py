from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from study.models import Organization, Topic
from study.ai_service import generate_interview_brief_with_claude, mock_interview_turn_with_claude, mock_interview_evaluate_with_claude

User = get_user_model()

class Command(BaseCommand):
    help = "Seeds starter target organizations with generated AI briefs and mock interview history"

    def handle(self, *args, **options):
        user = User.objects.filter(is_superuser=True).first() or User.objects.first()
        if not user:
            self.stdout.write(self.style.WARNING("No user found in database. Skipping organization seeding."))
            return

        self.stdout.write(f"Seeding organizations for user: {user.username}")

        # 1. AWS Role
        org_aws, created_aws = Organization.objects.update_or_create(
            user=user,
            company_name="Amazon Web Services (AWS)",
            defaults={
                "role": "Solutions Architect - Cloud Infrastructure",
                "status": "Interviewing",
                "company_url": "https://aws.amazon.com",
                "job_posting_url": "https://amazon.jobs/en/jobs/AWS-SA-Associate",
                "notes": "Targeting cloud infrastructure modernization, multi-AZ high availability, and hybrid cloud connectivity.",
            }
        )
        self.stdout.write("Generating brief for AWS...")
        generate_interview_brief_with_claude(org_aws, raw_text="We require deep hands-on expertise in AWS VPC peering, Transit Gateway, RDS Multi-AZ failover, Route 53 latency routing, and Terraform automation.", user=user)

        # 2. Cisco Systems Role
        org_cisco, created_cisco = Organization.objects.update_or_create(
            user=user,
            company_name="Cisco Systems",
            defaults={
                "role": "Network Consulting Engineer",
                "status": "Interviewing",
                "company_url": "https://www.cisco.com",
                "job_posting_url": "https://jobs.cisco.com/jobs/network-consulting-engineer",
                "notes": "Enterprise campus networking, OSPF/BGP routing protocols, 802.1Q trunking, and network security automation.",
            }
        )
        self.stdout.write("Generating brief for Cisco...")
        generate_interview_brief_with_claude(org_cisco, raw_text="Candidate must master Cisco IOS-XE command line, OSPF neighbor states, VLAN trunking, Access Control Lists, and Python network scripting.", user=user)

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded target organizations: {org_aws.company_name}, {org_cisco.company_name}"))
