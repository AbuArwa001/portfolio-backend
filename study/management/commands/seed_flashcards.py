from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from study.models import StudyCertification, Topic, Flashcard

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds initial high-yield flashcards for CCNA and AWS SAA-C03 with SM-2 spaced repetition parameters"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding high-yield flashcards..."))

        superusers = list(User.objects.filter(is_superuser=True))
        if not superusers:
            self.stdout.write(self.style.WARNING("No superusers found. Falling back to all users."))
            superusers = list(User.objects.all())

        if not superusers:
            self.stdout.write(self.style.ERROR("No users found to assign flashcards to."))
            return

        ccna = StudyCertification.objects.filter(code="CCNA-200-301").first()
        aws = StudyCertification.objects.filter(code="AWS-SAA-C03").first()

        cards_seeded = 0

        # CCNA Flashcards
        if ccna:
            ccna_cards = [
                (
                    "1.1",
                    "What is the usable host formula for an IPv4 subnet with prefix length /28?",
                    "Prefix /28 leaves 4 host bits (32 - 28 = 4). Total addresses = 2^4 = 16. Usable hosts = 2^4 - 2 = 14 usable IP addresses (subtract network address and directed broadcast address)."
                ),
                (
                    "1.1",
                    "List the default Administrative Distances (AD) for Connected, Static, eBGP, EIGRP, OSPF, and RIP.",
                    "Connected: 0\nStatic: 1\neBGP: 20\nEIGRP (Internal): 90\nOSPF: 110\nRIP: 120\nExternal EIGRP: 170\niBGP: 200"
                ),
                (
                    "2.1",
                    "What happens to untagged traffic entering an 802.1Q trunk port?",
                    "Untagged frames entering an 802.1Q trunk are assigned to the configured Native VLAN (default VLAN 1). For security, best practice is to configure an unused VLAN (e.g. VLAN 999) as native on both ends to mitigate VLAN hopping."
                ),
                (
                    "2.4",
                    "What are the channel-group modes for LACP (802.3ad) versus PAgP (Cisco proprietary)?",
                    "LACP (802.3ad standard): 'active' (initiates negotiation) and 'passive' (responds only).\nPAgP (Cisco): 'desirable' (initiates negotiation) and 'auto' (responds only).\n'on' forces EtherChannel without negotiation (must match 'on' on peer)."
                ),
                (
                    "2.5",
                    "What are the port states in 802.1w Rapid Spanning Tree Protocol (RSTP)?",
                    "RSTP collapses 802.1D's 5 states into 3 states:\n1. Discarding (combines Disabled, Blocking, and Listening)\n2. Learning\n3. Forwarding"
                ),
                (
                    "3.4",
                    "In OSPFv2, what criteria determine the Router ID (RID) when not explicitly configured?",
                    "1. Highest IP address on an active Loopback interface.\n2. If no loopbacks exist, highest IP address on an active physical interface.\nBest practice: Explicitly configure with 'router-id x.x.x.x'."
                ),
                (
                    "4.1",
                    "What is the difference between Dynamic NAT and Port Address Translation (PAT / NAT Overload)?",
                    "Dynamic NAT maps private IPs to a pool of public IPs 1-to-1 (exhausts pool when hosts > pool IPs).\nPAT (NAT Overload) maps multiple private IPs to a single public IP by multiplexing unique L4 source port numbers (up to ~64,000 concurrent sessions per IP)."
                ),
                (
                    "5.4",
                    "Where should Standard IPv4 ACLs versus Extended IPv4 ACLs be placed in the network?",
                    "Standard ACLs (filter on source IP only, numbers 1-99 & 1300-1999): Place as close to the DESTINATION as possible.\nExtended ACLs (filter on source, dest, protocol, and port, numbers 100-199 & 2000-2699): Place as close to the SOURCE as possible to conserve bandwidth."
                ),
            ]

            for ref, front, back in ccna_cards:
                topic = Topic.objects.filter(certification=ccna, blueprint_ref=ref).first()
                if not topic:
                    continue
                for u in superusers:
                    Flashcard.objects.update_or_create(
                        user=u,
                        topic=topic,
                        front=front,
                        defaults={
                            "back": back,
                            "repetition_level": 0,
                            "interval_days": 1,
                            "ease_factor": 2.50,
                            "due_date": timezone.now().date(),
                        }
                    )
                    cards_seeded += 1

        # AWS Flashcards
        if aws:
            aws_cards = [
                (
                    "1.3",
                    "How do Security Groups differ from Network ACLs (NACLs) in terms of state and evaluation?",
                    "Security Groups: Stateful (return traffic automatically allowed regardless of outbound rules), instance-level (ENI), allow rules only (implicit deny all).\nNetwork ACLs: Stateless (return traffic must be explicitly permitted), subnet-level, numbered rule evaluation (lowest number first), supports both Allow and Deny rules."
                ),
                (
                    "2.1",
                    "In an Application Load Balancer (ALB), what is Cross-Zone Load Balancing and how is it billed?",
                    "Cross-Zone Load Balancing distributes incoming requests evenly across all registered targets in all enabled AZs. On ALBs, cross-zone load balancing is always ENABLED by default at NO extra charge. On NLBs, it is disabled by default and incurs inter-AZ data charges if enabled."
                ),
                (
                    "2.3",
                    "Compare Amazon RDS Multi-AZ Standby vs Read Replicas across replication, purpose, and engine support.",
                    "Multi-AZ: Synchronous replication, primary purpose is High Availability / Automated Failover (<60s), standby cannot be queried, same region only.\nRead Replica: Asynchronous replication, primary purpose is Read Scaling, can be queried, supports up to 15 replicas, can be cross-region or cross-account."
                ),
                (
                    "3.4",
                    "Explain the SNS Fanout architecture pattern.",
                    "An event publisher publishes a message to a single Amazon SNS Topic. Multiple Amazon SQS queues are subscribed to the topic. SNS pushes an identical copy of the message asynchronously to all subscribed queues simultaneously, allowing independent microservices (e.g. billing, shipping, analytics) to consume without coupling."
                ),
                (
                    "1.6",
                    "Why choose Origin Access Control (OAC) over Origin Access Identity (OAI) for CloudFront with S3?",
                    "OAC supports:\n1. Server-Side Encryption with AWS KMS (SSE-KMS) - OAI cannot.\n2. All HTTP methods (PUT, POST, DELETE) - OAI only supports GET/HEAD.\n3. Works in all AWS regions (including opt-in regions).\n4. Adheres to SigV4 authentication."
                ),
                (
                    "4.1",
                    "What are the minimum storage duration and minimum billable object size for S3 Standard-IA?",
                    "Minimum storage duration: 30 days (deleting earlier incurs prorated charge).\nMinimum billable object size: 128 KB (objects < 128KB are billed as 128KB).\nHas a per-GB data retrieval fee."
                ),
                (
                    "1.5",
                    "How does Envelope Encryption work in AWS KMS?",
                    "1. AWS KMS generates a 256-bit plaintext Data Key and an encrypted Data Key under the KMS Customer Master Key (CMK).\n2. Application encrypts plaintext data locally in memory using the plaintext Data Key.\n3. Application securely deletes the plaintext Data Key from memory and stores the encrypted data alongside the encrypted Data Key.\n4. KMS never stores the Data Key."
                ),
                (
                    "3.5",
                    "What is the maximum execution duration for an AWS Lambda function?",
                    "15 minutes (900 seconds). For tasks running longer than 15 minutes, use AWS Step Functions, Amazon ECS on AWS Fargate, or AWS Batch."
                ),
            ]

            for ref, front, back in aws_cards:
                topic = Topic.objects.filter(certification=aws, blueprint_ref=ref).first()
                if not topic:
                    continue
                for u in superusers:
                    Flashcard.objects.update_or_create(
                        user=u,
                        topic=topic,
                        front=front,
                        defaults={
                            "back": back,
                            "repetition_level": 0,
                            "interval_days": 1,
                            "ease_factor": 2.50,
                            "due_date": timezone.now().date(),
                        }
                    )
                    cards_seeded += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {cards_seeded} flashcard assignments across {len(superusers)} users!"))
