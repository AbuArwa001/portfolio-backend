"""
Automated Database Provisioning and Seeding Script for Portfolio
Compatible with both local SQLite and Neon PostgreSQL.
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model
from users.models import UserProfile, SkillCategory, Skill
from projects.models import Project
from references.models import Reference
from certifications.models import Certification
from blog.models import BlogPost

User = get_user_model()

def run_migrations():
    print("=" * 60)
    print("Running Django database migrations...")
    call_command("makemigrations", "blog", interactive=False)
    call_command("migrate", interactive=False)
    print("Migrations completed successfully.")

def seed_admin_user():
    print("=" * 60)
    print("Seeding Administrator User...")
    admin_user, created = User.objects.get_or_create(
        username="admin",
        defaults={
            "email": "khalfan@khalfanathman.dev",
            "first_name": "Khalfan",
            "last_name": "Athman",
            "is_staff": True,
            "is_superuser": True,
        }
    )
    admin_user.email = "khalfan@khalfanathman.dev"
    admin_user.first_name = "Khalfan"
    admin_user.last_name = "Athman"
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.set_password("Admin@Portfolio2026!")
    admin_user.save()

    # Also ensure secondary username lookup (khalfan / AbuArwa001) aliases exist if desired
    khalfan_user, _ = User.objects.get_or_create(
        username="khalfan",
        defaults={
            "email": "khalfan.alt@khalfanathman.dev",
            "first_name": "Khalfan",
            "last_name": "Athman",
            "is_staff": True,
            "is_superuser": True,
        }
    )
    khalfan_user.set_password("Admin@Portfolio2026!")
    khalfan_user.save()

    # UserProfile
    profile, _ = UserProfile.objects.get_or_create(user=admin_user)
    profile.title = "Network Engineer & Full-Stack Developer"
    profile.bio = (
        "Software Engineer with backend specialization in Django REST Framework and "
        "high-performance Next.js frontends, backed by 6+ years of network engineering discipline. "
        "Certified in AWS, Oracle Cloud (OCI), and experienced in designing scalable systems."
    )
    profile.location = "Nairobi, Kenya"
    profile.phone = "+254719401851"
    profile.website = "https://khalfanathman.dev"
    profile.github = "https://github.com/AbuArwa001"
    profile.linkedin = "https://www.linkedin.com/in/khalfaniathman"
    profile.save()
    print("Admin user verified: username='admin', email='khalfan@khalfanathman.dev'")
    return admin_user

def seed_projects(user):
    print("=" * 60)
    print("Seeding Portfolio Projects...")

    projects_data = [
        {
            "name": "Langata Islamic Center",
            "description": (
                "End-to-end web platform and digital hub for the Langata Islamic Center & Mosque. "
                "Includes real-time donation drives, community announcements, prayer schedules, "
                "event management, and programme listings with a decoupled Next.js frontend and DRF API."
            ),
            "link": "https://www.langataislamiccenter.org/",
            "status": "Live",
            "completion": "100%",
            "technologies": "Next.js 15, TypeScript, Django REST Framework, PostgreSQL, Tailwind CSS",
            "type": "Web App",
        },
        {
            "name": "SUPKEM Digital Portal",
            "description": (
                "National digital presence for the Supreme Council of Kenya Muslims. "
                "Features a bi-lingual (EN/AR) news publishing engine, executive leadership showcase, "
                "secure admin portal with Excel export, and a national Quran Competition registration portal."
            ),
            "link": "https://www.supkem.org/",
            "status": "Live",
            "completion": "100%",
            "technologies": "Next.js 15, Django REST Framework, PostgreSQL, next-intl, Tailwind CSS, JWT",
            "type": "Web App",
        },
        {
            "name": "jamiaGive Admin Dashboard",
            "description": (
                "Enterprise administrative dashboard for Jamia Mosque Nairobi's charitable operations. "
                "Includes real-time fund tracking, structured appeal categories, scheduled drives, "
                "secure inter-account transfers, and financial audit logs powered by a decoupled DRF API."
            ),
            "link": "https://jmc-admin-dashboard.vercel.app/",
            "status": "In Progress",
            "completion": "85%",
            "technologies": "Next.js, TypeScript, Django REST Framework, PostgreSQL, Radix UI, Tailwind CSS",
            "type": "Web App",
        },
        {
            "name": "SeaFood Platform & Analytics Dashboard",
            "description": (
                "Full-stack seafood supply commerce platform featuring an executive analytics dashboard. "
                "Delivers inventory management, product cataloguing, order fulfilment tracking, "
                "and real-time revenue visualisations."
            ),
            "link": "https://seafooddashboard.vercel.app/",
            "status": "Live",
            "completion": "100%",
            "technologies": "Next.js, TypeScript, Python, Django REST Framework, Recharts, PostgreSQL",
            "type": "Web App",
        },
        {
            "name": "Religious Attaché KSA",
            "description": (
                "Production platform for the Kenya Religious Attaché office in Saudi Arabia. "
                "Handles diplomatic service requests, news publishing, and official community announcements."
            ),
            "link": "https://www.religiousattacheksa.co.ke/en",
            "status": "Live",
            "completion": "100%",
            "technologies": "Next.js, Django REST Framework, PostgreSQL, Python, Nginx",
            "type": "Web App",
        },
        {
            "name": "Kuranet — Voting System API",
            "description": (
                "Secure distributed voting API architecture featuring high availability behind HAProxy load balancers, "
                "JWT authentication, database replication, rate limiting, and DDoS protection."
            ),
            "link": "https://github.com/AbuArwa001/kuranet",
            "status": "Completed",
            "completion": "100%",
            "technologies": "Python, Flask, HAProxy, MySQL, JWT, Nginx, AWS",
            "type": "API / Backend",
        },
    ]

    for pdata in projects_data:
        p, created = Project.objects.get_or_create(
            name=pdata["name"],
            defaults={**pdata, "user": user}
        )
        if not created:
            for k, v in pdata.items():
                setattr(p, k, v)
            p.user = user
            p.save()
        print(f"  - Project: {p.name} ({p.status})")

def seed_skills(user):
    print("=" * 60)
    print("Seeding Skills & Categories...")

    categories_data = [
        {
            "name": "Backend & APIs",
            "skills": [
                ("Python / Django & DRF", 95),
                ("REST API Design & Swagger", 92),
                ("PostgreSQL & Database Design", 88),
                ("Flask & Celery", 82),
            ],
        },
        {
            "name": "Frontend & Web",
            "skills": [
                ("Next.js 15 & React 19", 90),
                ("TypeScript & Modern JS", 88),
                ("Tailwind CSS & Shadcn/UI", 94),
                ("Framer Motion & Animations", 85),
            ],
        },
        {
            "name": "Networking & Infrastructure",
            "skills": [
                ("TCP/IP & Routing Protocols", 94),
                ("Network Security & Firewalls", 88),
                ("Cisco Routers & Switches", 85),
                ("Wireshark & Packet Analysis", 86),
            ],
        },
        {
            "name": "Cloud & DevOps",
            "skills": [
                ("Linux System Administration", 92),
                ("Docker & Containerization", 85),
                ("AWS Cloud (EC2, S3, RDS)", 82),
                ("Nginx, Gunicorn & CI/CD", 86),
            ],
        },
        {
            "name": "Systems & Core",
            "skills": [
                ("C Programming & POSIX", 84),
                ("Bash & Shell Scripting", 88),
                ("Git & Collaborative Workflows", 92),
            ],
        },
    ]

    profile = user.profile
    for cat_data in categories_data:
        cat, _ = SkillCategory.objects.get_or_create(name=cat_data["name"])
        profile.skill_categories.add(cat)
        for s_name, s_level in cat_data["skills"]:
            skill, _ = Skill.objects.get_or_create(
                name=s_name,
                category=cat,
                defaults={"level": s_level}
            )
            skill.level = s_level
            skill.save()
            print(f"  - Skill: {skill.name} ({skill.level}%) in {cat.name}")

def seed_certifications(user):
    print("=" * 60)
    print("Seeding Certifications...")

    certs_data = [
        {
            "name": "AWS Certified Cloud Practitioner",
            "issuer": "Amazon Web Services",
            "date": "2023-08-15",
            "in_progress": False,
            "type": "aws",
            "credential_url": "https://www.credly.com/",
        },
        {
            "name": "Oracle Cloud Infrastructure (OCI) Associate",
            "issuer": "Oracle",
            "date": "2023-01-20",
            "in_progress": False,
            "type": "oracle",
            "credential_url": "https://catalog-education.oracle.com/",
        },
        {
            "name": "Certificate in Software Engineering (ALX)",
            "issuer": "ALX Africa",
            "date": "2024-10-01",
            "in_progress": False,
            "type": "alx",
            "credential_url": "https://alxafrica.com",
        },
        {
            "name": "AWS Certified Solutions Architect – Associate",
            "issuer": "Amazon Web Services",
            "date": "2025-01-01",
            "in_progress": True,
            "type": "aws",
            "credential_url": "",
        },
        {
            "name": "Cisco Certified Network Associate (CCNA Routing & Switching)",
            "issuer": "Cisco",
            "date": "2024-06-10",
            "in_progress": False,
            "type": "badge",
            "credential_url": "https://www.cisco.com/",
        },
    ]

    for cdata in certs_data:
        cert, created = Certification.objects.get_or_create(
            name=cdata["name"],
            defaults={**cdata, "user": user}
        )
        if not created:
            for k, v in cdata.items():
                setattr(cert, k, v)
            cert.user = user
            cert.save()
        print(f"  - Certification: {cert.name} ({cert.issuer})")

def seed_references():
    print("=" * 60)
    print("Seeding Professional References...")

    refs_data = [
        {
            "name": "Eng. Ahmed Salim",
            "title": "Lead Infrastructure Architect",
            "company": "SUPKEM ICT Directorate",
            "relationship": "Project Director & Technical Overseer",
            "quote": "Khalfan engineered our national digital portal with remarkable reliability. His mastery of both network infrastructure and decoupled web applications delivered a system that effortlessly handled hundreds of concurrent event registrations.",
            "email": "ahmed.salim@supkem.org",
            "phone": "+254 722 000 111",
            "linkedin": "https://linkedin.com",
        },
        {
            "name": "Dr. Hassan Omar",
            "title": "Director of Operations",
            "company": "Langata Islamic Center",
            "relationship": "Client & Executive Supervisor",
            "quote": "The digital portal Khalfan built for the Langata Islamic Center brought clarity, transparency, and elegance to our community programmes and real-time donations. Outstanding work ethic and technical precision.",
            "email": "director@langataislamiccenter.org",
            "phone": "+254 733 111 222",
            "linkedin": "https://linkedin.com",
        },
        {
            "name": "Zubair Mohamed",
            "title": "Head of Charitable Funds",
            "company": "Jamia Mosque Committee",
            "relationship": "Project Lead for jamiaGive",
            "quote": "Khalfan's work on the jamiaGive administrative dashboard revolutionized our donation reporting and category management. The security and performance of the DRF backend are second to none.",
            "email": "admin@jmc.org",
            "phone": "+254 711 222 333",
            "linkedin": "https://linkedin.com",
        },
    ]

    for rdata in refs_data:
        ref, created = Reference.objects.get_or_create(
            name=rdata["name"],
            defaults=rdata
        )
        if not created:
            for k, v in rdata.items():
                setattr(ref, k, v)
            ref.save()
        print(f"  - Reference: {ref.name} — {ref.company}")

def seed_blog_posts():
    print("=" * 60)
    print("Seeding Technical Blog Posts...")

    posts_data = [
        {
            "title": "Architecting Decoupled Next.js 15 & Django REST APIs for Scale",
            "slug": "architecting-decoupled-nextjs-and-django-apis",
            "content": """Building high-performance web platforms requires a clean separation of concerns. In this article, we explore the architectural decisions behind coupling Next.js 15 App Router with a stateless Django REST Framework (DRF) backend.

### Key Architectural Tenets
1. **Stateless JWT Authentication**: Keeping session state out of the database tier enables seamless horizontal scaling across instances.
2. **Reverse Proxying and SSL Termination**: Utilizing Nginx and Cloudflare for SSL offloading and rate limiting.
3. **Database Connection Pooling**: Preventing connection exhaustion when connecting serverless frontends to PostgreSQL.

When properly decoupled, each layer can be optimized, deployed, and scaled independently without bottlenecks.""",
        },
        {
            "title": "Network Engineering Principles Every Backend Developer Should Know",
            "slug": "network-engineering-principles-for-backend-devs",
            "content": """Software performance doesn't stop at the application layer. Understanding OSI Layer 3 through Layer 7 routing, TCP window scaling, and DNS propagation changes the way you write backend code.

### Core Concepts:
- **TCP Three-Way Handshake & Keep-Alives**: How persistent HTTP/2 and connection reuse cut latency by over 60%.
- **Subnetting & VPC Isolation**: Protecting database clusters with private subnets and security group ingress rules.
- **Bufferbloat & MTU Sizing**: Why packet fragmentation causes subtle timeout issues in high-throughput microservices.

A disciplined network perspective ensures that backend services remain resilient even under challenging network conditions.""",
        },
    ]

    for pdata in posts_data:
        post, created = BlogPost.objects.get_or_create(
            slug=pdata["slug"],
            defaults=pdata
        )
        if not created:
            for k, v in pdata.items():
                setattr(post, k, v)
            post.save()
        print(f"  - Blog Post: {post.title}")

def main():
    print("\nStarting Portfolio Database Setup & Seeding...")
    run_migrations()
    user = seed_admin_user()
    seed_projects(user)
    seed_skills(user)
    seed_certifications(user)
    seed_references()
    seed_blog_posts()
    print("\n" + "=" * 60)
    print("PORTFOLIO DATABASE SETUP COMPLETE!")
    print("Admin Credentials:")
    print("  Username / Email: admin OR khalfan@khalfanathman.dev")
    print("  Password:         Admin@Portfolio2026!")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
