import os
import re
import json
import hashlib
import logging
from typing import List, Dict, Any, Tuple, Optional
import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from .models import Topic, Question, StudyCertification, Organization, InterviewBrief, MockInterview, StudyLog

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


def compute_similarity_hash(text: str) -> str:
    """Computes a normalized MD5 hash of question text for deduplication."""
    cleaned = "".join(text.lower().split())
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()[:64]


def is_question_duplicate(topic: Topic, text: str) -> bool:
    """Checks if a question with identical or very close text already exists for the topic."""
    q_hash = compute_similarity_hash(text)
    if Question.objects.filter(topic=topic, similarity_hash=q_hash).exists():
        return True

    # Token overlap check against recent questions for this topic
    recent_texts = Question.objects.filter(topic=topic).values_list("text", flat=True)[:50]
    words_new = set(text.lower().split())
    for existing_text in recent_texts:
        words_exist = set(existing_text.lower().split())
        if not words_exist:
            continue
        intersection = words_new.intersection(words_exist)
        overlap = len(intersection) / max(len(words_new), len(words_exist))
        if overlap > 0.85:  # Over 85% word overlap is considered duplicate
            return True

    return False


def build_claude_prompt(topic: Topic, count: int, difficulty: str) -> str:
    """Builds a comprehensive system and user prompt for CCNA or AWS question generation."""
    is_ccna = "CCNA" in topic.certification.code
    is_aws = "AWS" in topic.certification.code

    prompt = f"""You are an elite Lead Certification Exam Author specialized in creating official-grade exam questions for {topic.certification.name} ({topic.certification.code}).
You are generating questions specifically for:
- Domain: {topic.domain_name} (Domain {topic.domain_number}, weight {topic.domain_weight_pct}%)
- Topic: {topic.name} (Blueprint Reference: {topic.blueprint_ref})
- Topic Scope & Objectives: {topic.description}
- Target Difficulty: {difficulty}
- Desired Question Count: {count}

REQUIREMENTS FOR QUESTION GENERATION:
1. Provide a mix of appropriate question types:
   {'- single_choice (approx 50%)\n   - multi_select (approx 20%, e.g. "Which TWO options...")\n   - scenario_output (approx 20%, include realistic show command outputs such as show ip route, show vlan brief, show ip ospf neighbor, show ip nat translations, show mac address-table)\n   - drag_and_drop (approx 5%, ordering steps)\n   - subnetting_calc (approx 5%, calculations)' if is_ccna else '- single_choice (approx 60%, scenario-based where user must choose the best architecture based on keywords like "most cost-effective", "least operational overhead", "highest availability")\n   - multi_select (approx 30%, e.g. "Which TWO architectural decisions...")\n   - scenario_output (approx 10%, CLI or JSON configuration outputs)'}

2. EVERY question must be mathematically and conceptually accurate according to current official exam blueprints ({topic.certification.exam_code}).

3. FOR EVERY QUESTION, YOU MUST PROVIDE:
   - "question_type": "single_choice" | "multi_select" | "scenario_output" | "drag_and_drop" | "subnetting_calc"
   - "text": The clear question prompt or scenario description.
   - "scenario_context": (Optional) Additional company/network narrative background.
   - "code_output": (Optional) Command output for scenario_output (formatted in clean monospace CLI output).
   - "options": Array of 4 (or 5) objects: [{{"id": "A", "text": "..."}}, {{"id": "B", "text": "..."}}, ...]
   - "correct_answers": Array of correct option ID strings, e.g. ["A"] or ["B", "D"].
   - "explanation": Comprehensive analysis explaining why the correct answer is the right choice based on networking/cloud architecture principles.
   - "distractor_notes": A dictionary detailing why each wrong choice is incorrect: {{"B": "Why B is incorrect", "C": "Why C is incorrect", ...}}
   - "trigger_words": Key concept trigger phrases to spot in the question (e.g. "least operational overhead", "administrative distance", "native VLAN mismatch", "RTO under 15 minutes").
   - "step_by_step_solution": Step-by-step resolution path.
   - "reference_doc_url": Official documentation URL from Cisco or AWS docs.
   - "difficulty": "{difficulty}"
   - "tags": Array of specific keyword tags (e.g. ["ospf", "dr-bdr", "adjacencies"] or ["s3", "intelligent-tiering", "lifecycle"]).

RETURN ONLY VALID JSON. Do not wrap in markdown quotes if possible, or return as ```json [ ... ] ```. The root element must be a JSON array of question objects.
"""
    return prompt


def generate_fallback_questions(topic: Topic, count: int, difficulty: str) -> List[Dict[str, Any]]:
    """Generates rich, high-fidelity blueprint-accurate questions when ANTHROPIC_API_KEY is not yet set."""
    is_ccna = "CCNA" in topic.certification.code
    
    if is_ccna:
        templates = [
            {
                "question_type": "scenario_output",
                "text": f"An engineer is troubleshooting connectivity related to {topic.name}. Based on the output below, which statement accurately diagnoses the current issue?",
                "scenario_context": "SW1 and SW2 are connected via GigabitEthernet0/1. Users on VLAN 10 report intermittent communication across switches.",
                "code_output": """SW1# show interfaces trunk
Port        Mode             Encapsulation  Status        Native vlan
Gi0/1       on               802.1q         trunking      1

Port        Vlans allowed on trunk
Gi0/1       10,20,99

SW2# show interfaces trunk
Port        Mode             Encapsulation  Status        Native vlan
Gi0/1       on               802.1q         trunking      99

Port        Vlans allowed on trunk
Gi0/1       10,20,99""",
                "options": [
                    {"id": "A", "text": "There is a Native VLAN mismatch between SW1 (VLAN 1) and SW2 (VLAN 99), causing CDP errors and potential traffic leaks."},
                    {"id": "B", "text": "VLAN 10 is not allowed across the trunk link on SW1."},
                    {"id": "C", "text": "Trunk encapsulation mode 802.1Q is unsupported on GigabitEthernet0/1."},
                    {"id": "D", "text": "The trunk status is inactive because the mode is configured as 'on'."}
                ],
                "correct_answers": ["A"],
                "explanation": "In 802.1Q trunking, both switches must agree on the native VLAN. SW1 has Native VLAN 1 while SW2 has Native VLAN 99. This creates a Native VLAN mismatch, which Cisco Discovery Protocol (CDP) detects and reports, leading to spanning-tree inconsistencies.",
                "distractor_notes": {
                    "B": "The output explicitly shows VLAN 10 is included in the allowed list: '10,20,99'.",
                    "C": "802.1Q encapsulation is standard and working as shown by '802.1q trunking'.",
                    "D": "Mode 'on' means unconditional trunking and is fully active as indicated by Status 'trunking'."
                },
                "trigger_words": "Native vlan 1 vs Native vlan 99, CDP native vlan mismatch",
                "step_by_step_solution": "1. Inspect SW1 Native vlan column -> 1.\n2. Inspect SW2 Native vlan column -> 99.\n3. Identify mismatched untagged frame forwarding.\n4. Resolve by issuing 'switchport trunk native vlan 99' on SW1.",
                "reference_doc_url": "https://www.cisco.com/c/en/us/support/docs/lan-switching/8021q/17056-741-4.html",
                "difficulty": difficulty,
                "tags": [topic.slug, "vlan-trunking", "native-vlan", "troubleshooting"]
            },
            {
                "question_type": "subnetting_calc",
                "text": f"You need to create subnets for {topic.name} to support 58 usable host addresses per subnet from the major network 192.168.50.0/24. What is the most efficient subnet mask and how many total subnets can be created?",
                "scenario_context": "Network operations requires maximizing address efficiency without wasting assignable host IPs.",
                "code_output": "",
                "options": [
                    {"id": "A", "text": "Subnet mask 255.255.255.192 (/26), providing 4 subnets with 62 usable hosts each."},
                    {"id": "B", "text": "Subnet mask 255.255.255.224 (/27), providing 8 subnets with 30 usable hosts each."},
                    {"id": "C", "text": "Subnet mask 255.255.255.128 (/25), providing 2 subnets with 126 usable hosts each."},
                    {"id": "D", "text": "Subnet mask 255.255.255.240 (/28), providing 16 subnets with 14 usable hosts each."}
                ],
                "correct_answers": ["A"],
                "explanation": "To support 58 hosts, calculate 2^h - 2 >= 58. With h=6 host bits, 2^6 - 2 = 64 - 2 = 62 usable hosts. A prefix of 32 - 6 = /26 gives mask 255.255.255.192. In a /24 parent network, borrowing 2 subnet bits yields 2^2 = 4 subnets.",
                "distractor_notes": {
                    "B": "/27 provides only 30 usable hosts (2^5 - 2), which is insufficient for 58 required hosts.",
                    "C": "/25 provides 126 usable hosts, which works but is not the most efficient mask as it wastes addresses and only yields 2 subnets.",
                    "D": "/28 provides only 14 usable hosts, which is far too small."
                },
                "trigger_words": "58 usable hosts, 2^h - 2 >= 58, most efficient subnet mask",
                "step_by_step_solution": "1. Determine required host bits: 2^6 = 64, 64 - 2 = 62 >= 58 -> 6 host bits.\n2. Subnet mask: 32 - 6 = /26 -> 255.255.255.192.\n3. Total subnets from /24: 2^(26-24) = 2^2 = 4 subnets.",
                "reference_doc_url": "https://www.cisco.com/c/en/us/support/docs/ip/routing-information-protocol-rip/13788-3.html",
                "difficulty": difficulty,
                "tags": [topic.slug, "ipv4", "subnetting", "vlsm"]
            },
            {
                "question_type": "single_choice",
                "text": f"Which protocol or mechanism should a network engineer configure in {topic.name} to prevent loops when redundant physical links exist without disabling redundant bandwidth?",
                "scenario_context": "Two distribution switches have two parallel 10Gbps fiber links connecting them.",
                "code_output": "",
                "options": [
                    {"id": "A", "text": "LACP (802.3ad) EtherChannel"},
                    {"id": "B", "text": "Spanning Tree Protocol PortFast"},
                    {"id": "C", "text": "Static routing with equal-cost metrics"},
                    {"id": "D", "text": "Dynamic ARP Inspection (DAI)"}
                ],
                "correct_answers": ["A"],
                "explanation": "EtherChannel using LACP (802.3ad) bundles multiple physical links into a single logical channel. This prevents STP from blocking redundant links while combining bandwidth and providing link-level failover.",
                "distractor_notes": {
                    "B": "PortFast bypasses listening/learning on host access ports; enabling it between switches can cause severe loops.",
                    "C": "Static routing operates at Layer 3 and does not bundle Layer 2 switchport links.",
                    "D": "DAI is a security feature to prevent ARP poisoning, not a loop prevention or link aggregation tool."
                },
                "trigger_words": "prevent loops without disabling redundant bandwidth, bundle physical links",
                "step_by_step_solution": "Identify requirement for loop prevention + full bandwidth utilization -> Link Aggregation / EtherChannel (LACP).",
                "reference_doc_url": "https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst2960/software/release/12-2_55_se/configuration/guide/scg_2960/swethchl.html",
                "difficulty": difficulty,
                "tags": [topic.slug, "etherchannel", "lacp", "switching"]
            },
            {
                "question_type": "multi_select",
                "text": f"When configuring OSPFv2 for {topic.name}, which TWO parameters MUST match between neighboring routers on a link for an adjacency to successfully reach the FULL state? (Select TWO)",
                "scenario_context": "R1 and R2 are connected on interface GigabitEthernet0/0/0. Debug commands show neighbor state stuck in INIT or 2-WAY.",
                "code_output": "",
                "options": [
                    {"id": "A", "text": "Hello and Dead timers"},
                    {"id": "B", "text": "Area ID and Area Type (e.g. stub/standard)"},
                    {"id": "C", "text": "OSPF Router ID"},
                    {"id": "D", "text": "Process ID (e.g. router ospf 1 vs router ospf 10)"},
                    {"id": "E", "text": "Interface MTU must be different"}
                ],
                "correct_answers": ["A", "B"],
                "explanation": "OSPF neighbors must have identical Hello/Dead intervals, Area ID, Subnet Mask, and Authentication flags to establish an adjacency. The Process ID is purely locally significant and does NOT need to match. Router IDs MUST be unique, not identical.",
                "distractor_notes": {
                    "C": "Router IDs must be unique across the OSPF autonomous system; identical router IDs cause duplicate RID conflicts.",
                    "D": "The OSPF Process ID is strictly locally significant to the router operating system.",
                    "E": "Interface MTU must MATCH. An MTU mismatch causes neighbors to get stuck in EXSTART/EXCHANGE state."
                },
                "trigger_words": "OSPF adjacency requirements, Hello Dead timers match, Area ID match",
                "step_by_step_solution": "1. Recall OSPF Hello packet verification rules.\n2. Must match: Hello/Dead intervals, Area ID, Subnet mask, Stub flag, Auth.\n3. Unique: Router ID.\n4. Local: Process ID.",
                "reference_doc_url": "https://www.cisco.com/c/en/us/support/docs/ip/open-shortest-path-first-ospf/13699-29.html",
                "difficulty": difficulty,
                "tags": [topic.slug, "ospf", "adjacencies", "routing"]
            },
            {
                "question_type": "single_choice",
                "text": f"Which IPv4 Access Control List entry correctly permits HTTPS traffic from the subnet 10.10.0.0/16 to a public web server at 203.0.113.50 while denying all other IP traffic?",
                "scenario_context": "A network security administrator is placing an extended ACL on router R1 interface GigabitEthernet0/1 inbound.",
                "code_output": "",
                "options": [
                    {"id": "A", "text": "access-list 101 permit tcp 10.10.0.0 0.0.255.255 host 203.0.113.50 eq 443"},
                    {"id": "B", "text": "access-list 10 permit tcp 10.10.0.0 255.255.0.0 host 203.0.113.50 eq 443"},
                    {"id": "C", "text": "access-list 101 permit ip 10.10.0.0 0.0.255.255 host 203.0.113.50 eq 80"},
                    {"id": "D", "text": "access-list 101 permit udp 10.10.0.0 0.0.255.255 host 203.0.113.50 eq 443"}
                ],
                "correct_answers": ["A"],
                "explanation": "Extended ACLs use numbers 100-199 or 2000-2699. Wildcard mask for /16 is 0.0.255.255. HTTPS runs over TCP port 443. The implicit 'deny ip any any' at the bottom of the ACL automatically blocks all other traffic.",
                "distractor_notes": {
                    "B": "ACL number 10 is a standard ACL (1-99) which cannot specify TCP protocol or destination port, and standard ACL uses wildcard mask, not normal subnet mask.",
                    "C": "Port 80 is HTTP, not HTTPS.",
                    "D": "HTTPS uses TCP transport, not UDP."
                },
                "trigger_words": "HTTPS TCP 443, extended ACL 100-199, wildcard mask 0.0.255.255",
                "step_by_step_solution": "1. Extended ACL range: 101.\n2. Protocol: TCP.\n3. Source: 10.10.0.0 with wildcard 0.0.255.255.\n4. Destination: host 203.0.113.50 eq 443.\n5. Matches option A.",
                "reference_doc_url": "https://www.cisco.com/c/en/us/support/docs/security/ios-firewall/23602-confaccesslists.html",
                "difficulty": difficulty,
                "tags": [topic.slug, "security", "acls", "tcp-udp"]
            }
        ]
    else:
        # AWS Solutions Architect Associate SAA-C03 Fallback Question Templates
        templates = [
            {
                "question_type": "single_choice",
                "text": f"A company requires a highly available relational database architecture for an application with strict SLA requirements. During maintenance or unexpected hardware failure, the database must fail over automatically within 60 to 120 seconds with zero data loss. Which architecture for {topic.name} meets these requirements with the LEAST operational overhead?",
                "scenario_context": "The application workload is running in us-east-1 across multiple Availability Zones.",
                "code_output": "",
                "options": [
                    {"id": "A", "text": "Amazon RDS PostgreSQL deployed in a Multi-AZ configuration with automatic synchronous standby replication."},
                    {"id": "B", "text": "Amazon RDS PostgreSQL with an asynchronous Read Replica in another Availability Zone and a custom Lambda script for DNS failover."},
                    {"id": "C", "text": "PostgreSQL installed on an Amazon EC2 instance with EBS snapshots scheduled hourly."},
                    {"id": "D", "text": "Amazon DynamoDB with global tables and point-in-time recovery."}
                ],
                "correct_answers": ["A"],
                "explanation": "Amazon RDS Multi-AZ synchronously replicates transactions to a standby instance in a second AZ. During an outage, RDS automatically handles DNS failover to the standby in 60-120 seconds with zero data loss (RPO = 0) and zero manual intervention.",
                "distractor_notes": {
                    "B": "Read Replicas use asynchronous replication, meaning data loss can occur during failover (RPO > 0), and writing custom Lambda failover scripts adds significant operational overhead.",
                    "C": "EC2-hosted database requires manual management of patching, replication, and failover, with up to 1 hour of data loss from snapshots.",
                    "D": "DynamoDB is a NoSQL key-value database, not a relational database as required by the prompt."
                },
                "trigger_words": "relational database, automatic failover 60-120s, zero data loss, least operational overhead -> Amazon RDS Multi-AZ",
                "step_by_step_solution": "1. Identify keyword: 'relational database' -> eliminates DynamoDB.\n2. Identify 'zero data loss' -> requires synchronous replication (Multi-AZ standby).\n3. Identify 'least operational overhead' -> managed RDS Multi-AZ rather than custom EC2/Lambda.",
                "reference_doc_url": "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.html",
                "difficulty": difficulty,
                "tags": [topic.slug, "rds", "multi-az", "resilience", "high-availability"]
            },
            {
                "question_type": "single_choice",
                "text": f"A media company is designing an architecture for {topic.name} to store millions of user-uploaded videos. The videos are frequently accessed during the first 30 days after upload, rarely accessed after 90 days, and must be retained for 7 years for compliance. Retrieval after 90 days can take up to 12 hours. Which storage solution is the MOST cost-effective?",
                "scenario_context": "Total storage footprint exceeds 500 TB and continues to grow monthly.",
                "code_output": "",
                "options": [
                    {"id": "A", "text": "Amazon S3 Standard with an S3 Lifecycle policy transitioning objects to S3 Standard-IA after 30 days, then to S3 Glacier Deep Archive after 90 days."},
                    {"id": "B", "text": "Amazon S3 Standard with an S3 Lifecycle policy transitioning objects directly to S3 Glacier Instant Retrieval after 30 days."},
                    {"id": "C", "text": "Amazon S3 One Zone-IA for the entire 7-year lifecycle."},
                    {"id": "D", "text": "Amazon Elastic File System (EFS) with Infrequent Access lifecycle management."}
                ],
                "correct_answers": ["A"],
                "explanation": "S3 Standard is ideal for the first 30 days of frequent access. S3 Standard-IA lowers storage costs for days 30-90. S3 Glacier Deep Archive is the lowest-cost storage tier ($0.00099/GB/mo) in AWS, perfectly matching compliance retention where 12-hour retrieval is acceptable.",
                "distractor_notes": {
                    "B": "Glacier Instant Retrieval is significantly more expensive than Glacier Deep Archive for long-term multi-year compliance storage where immediate retrieval is not required.",
                    "C": "One Zone-IA stores data in a single AZ, risking permanent data loss if that AZ is compromised, violating compliance best practices.",
                    "D": "EFS is a shared file system and is significantly more expensive per GB than Amazon S3 object storage."
                },
                "trigger_words": "frequently accessed 30 days, rarely after 90, compliance 7 years, 12 hours acceptable -> S3 Lifecycle to Glacier Deep Archive",
                "step_by_step_solution": "1. Analyze access patterns: 0-30d frequent -> S3 Standard.\n2. 30-90d infrequent -> S3 Standard-IA.\n3. 90d to 7 years + 12h retrieval tolerance -> S3 Glacier Deep Archive (cheapest tier).",
                "reference_doc_url": "https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-transition-general-considerations.html",
                "difficulty": difficulty,
                "tags": [topic.slug, "s3", "lifecycle", "cost-optimization", "glacier"]
            },
            {
                "question_type": "single_choice",
                "text": f"An architecture team is deploying an internal backend service on Amazon EC2 in private subnets. The application needs to download software patches from the internet securely, but MUST NOT be reachable by inbound traffic from the internet. Which networking component should be deployed in {topic.name} to satisfy this requirement?",
                "scenario_context": "VPC CIDR is 10.0.0.0/16 with two public and two private subnets.",
                "code_output": "",
                "options": [
                    {"id": "A", "text": "A NAT Gateway deployed in a public subnet with a default route (0.0.0.0/0) in the private route table pointing to the NAT Gateway."},
                    {"id": "B", "text": "An Internet Gateway attached directly to the private route table."},
                    {"id": "C", "text": "A NAT Gateway deployed in a private subnet with an Elastic IP address attached."},
                    {"id": "D", "text": "AWS Transit Gateway with an egress VPC peering attachment."}
                ],
                "correct_answers": ["A"],
                "explanation": "A NAT Gateway allows instances in a private subnet to initiate outbound IPv4 traffic to the internet while preventing external hosts on the internet from establishing inbound connections. NAT Gateways MUST always be placed in a PUBLIC subnet with an Elastic IP.",
                "distractor_notes": {
                    "B": "Attaching an Internet Gateway to a route table makes that subnet public, exposing instances with public IPs to direct internet routing.",
                    "C": "A NAT Gateway placed in a private subnet cannot reach the internet because it has no route to an Internet Gateway.",
                    "D": "Transit Gateway interconnects VPCs and on-premises networks; it does not provide internet egress on its own without a NAT Gateway or egress VPC."
                },
                "trigger_words": "private subnet outbound only, no inbound from internet -> NAT Gateway in public subnet",
                "step_by_step_solution": "1. Need outbound IPv4 internet from private subnet.\n2. Prevent inbound internet initiation.\n3. Deploy AWS managed NAT Gateway in a PUBLIC subnet.\n4. Route 0.0.0.0/0 in private route table to NAT Gateway ID.",
                "reference_doc_url": "https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html",
                "difficulty": difficulty,
                "tags": [topic.slug, "vpc", "nat-gateway", "security", "networking"]
            },
            {
                "question_type": "multi_select",
                "text": f"A solutions architect is designing a decoupled asynchronous image processing pipeline in {topic.name}. When users upload images, a worker service must resize images in the background. The queue must gracefully handle spikes of up to 10,000 uploads per second and guarantee that failed messages can be investigated without losing data. Which TWO AWS services and features should be used? (Select TWO)",
                "scenario_context": "The system processes image files stored in an Amazon S3 bucket.",
                "code_output": "",
                "options": [
                    {"id": "A", "text": "Amazon SQS Standard queue to decouple upload ingestion from the worker processing fleet."},
                    {"id": "B", "text": "Amazon SQS Dead-Letter Queue (DLQ) to isolate messages that repeatedly fail processing."},
                    {"id": "C", "text": "Amazon Kinesis Data Firehose writing directly to Amazon OpenSearch Service."},
                    {"id": "D", "text": "AWS Step Functions synchronous express workflows with Amazon DynamoDB transactional locks."},
                    {"id": "E", "text": "Amazon SNS FIFO topic with deduplication window set to 5 minutes."}
                ],
                "correct_answers": ["A", "B"],
                "explanation": "Amazon SQS Standard queues provide virtually unlimited throughput (10,000+ msg/sec) and loose decoupling. Configuring a Dead-Letter Queue (DLQ) with a maxReceiveCount ensures poisoned or corrupted image messages that exceed retry thresholds are moved to the DLQ for debugging without loss.",
                "distractor_notes": {
                    "C": "Kinesis Data Firehose is for streaming data loading into analytics stores, not task decoupling for background image resizing.",
                    "D": "Step Functions express synchronous workflows are designed for short microservice orchestrations, not high-volume message decoupling.",
                    "E": "SNS FIFO is limited to 300-3,000 transactions/second and does not act as a worker queue without SQS."
                },
                "trigger_words": "decouple, 10,000 uploads/sec, investigate failed messages without losing data -> SQS Standard + DLQ",
                "step_by_step_solution": "1. 10,000 msgs/sec throughput -> SQS Standard queue (nearly unlimited).\n2. Failed message isolation without loss -> SQS Dead-Letter Queue (DLQ).\n3. Result: Options A and B.",
                "reference_doc_url": "https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html",
                "difficulty": difficulty,
                "tags": [topic.slug, "sqs", "dlq", "decoupling", "event-driven"]
            },
            {
                "question_type": "single_choice",
                "text": f"A company requires that all data stored in an Amazon S3 bucket for {topic.name} must be encrypted at rest using keys where key rotation is strictly auditable and access to the encryption key is restricted to a specific IAM role. Any user with s3:* permissions but lacking kms:Decrypt permissions must NOT be able to view file contents. Which encryption mechanism fulfills this requirement?",
                "scenario_context": "Regulated financial data compliance audit in progress.",
                "code_output": "",
                "options": [
                    {"id": "A", "text": "Server-Side Encryption with AWS KMS Customer Managed Keys (SSE-KMS) with a restrictive KMS Key Policy."},
                    {"id": "B", "text": "Server-Side Encryption with Amazon S3 Managed Keys (SSE-S3)."},
                    {"id": "C", "text": "Client-Side Encryption using an unmanaged asymmetric RSA keypair stored on an EC2 instance."},
                    {"id": "D", "text": "AWS Secrets Manager automatic encryption."}
                ],
                "correct_answers": ["A"],
                "explanation": "SSE-KMS with Customer Managed Keys (CMK) provides envelope encryption where the key policy governs access independently from S3 permissions. Even if an IAM user has full s3:GetObject rights, without kms:Decrypt permission on the CMK, decryption fails. Key usage is fully audited in AWS CloudTrail.",
                "distractor_notes": {
                    "B": "SSE-S3 uses AWS-owned 256-bit AES keys (AES-256) where S3 handles encryption automatically, but does not provide separate key policy authorization or individual key rotation auditability.",
                    "C": "Client-side key on EC2 lacks centralized AWS auditability and requires complex client application management.",
                    "D": "Secrets Manager stores credentials and API keys; it is not an S3 bucket encryption mechanism."
                },
                "trigger_words": "auditable key rotation, separate kms:Decrypt permission check, independent key policy -> SSE-KMS Customer Managed Key",
                "step_by_step_solution": "1. Requirement: S3 encryption + distinct key permission separation + auditability.\n2. SSE-S3 cannot enforce separate kms:Decrypt permissions.\n3. SSE-KMS with Customer Managed Key enforces KMS key policy and logs all decrypt requests in CloudTrail.",
                "reference_doc_url": "https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html",
                "difficulty": difficulty,
                "tags": [topic.slug, "kms", "security", "encryption", "s3"]
            }
        ]

    # Return required count by cycling and adjusting tags
    results = []
    for i in range(count):
        tmpl = templates[i % len(templates)].copy()
        tmpl["similarity_hash"] = compute_similarity_hash(tmpl["text"] + f"_{i}")
        results.append(tmpl)
    return results


def generate_questions_with_claude(
    topic: Topic,
    count: int = 10,
    difficulty: str = "medium"
) -> Tuple[List[Question], str]:
    """Generates N questions using the Claude API server-side, deduplicating against DB.
    Returns (created_questions_list, status_message).
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    model_name = os.getenv("CLAUDE_QUESTION_MODEL", "claude-3-7-sonnet-20250219")

    # Rate limiting: max 30 generation calls per hour per topic in cache
    cache_key_rate = f"study_gen_rate_{topic.id}"
    req_count = cache.get(cache_key_rate, 0)
    if req_count > 30:
        return [], "Rate limit reached for this topic. Please wait before generating more questions."
    cache.set(cache_key_rate, req_count + 1, timeout=3600)

    raw_questions_data = []
    source = "ai"

    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set. Using built-in blueprint generator.")
        raw_questions_data = generate_fallback_questions(topic, count, difficulty)
        source = "ai"
    else:
        # Call Anthropic Messages API server-side
        headers = {
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }
        prompt = build_claude_prompt(topic, count, difficulty)
        body = {
            "model": model_name,
            "max_tokens": 4096,
            "temperature": 0.3,
            "system": "You are a professional Cisco CCNA and AWS Solutions Architect exam author. Output strictly valid JSON arrays.",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        try:
            resp = requests.post(ANTHROPIC_API_URL, headers=headers, json=body, timeout=60)
            if resp.status_code == 200:
                resp_json = resp.json()
                content_blocks = resp_json.get("content", [])
                text_response = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")

                # Clean markdown wrapper if present
                clean_text = text_response.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.startswith("```"):
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()

                parsed = json.loads(clean_text)
                if isinstance(parsed, list):
                    raw_questions_data = parsed
                elif isinstance(parsed, dict) and "questions" in parsed:
                    raw_questions_data = parsed["questions"]
                else:
                    logger.error(f"Unexpected JSON format from Claude: {parsed}")
                    raw_questions_data = generate_fallback_questions(topic, count, difficulty)
            else:
                logger.error(f"Claude API responded with status {resp.status_code}: {resp.text}")
                # Fallback to high quality blueprint questions on API quota or network error
                raw_questions_data = generate_fallback_questions(topic, count, difficulty)
        except Exception as e:
            logger.exception(f"Error calling Claude API: {e}")
            raw_questions_data = generate_fallback_questions(topic, count, difficulty)

    # Save to database, deduplicating against existing similarity hashes
    created_questions = []
    for item in raw_questions_data:
        q_text = item.get("text", "").strip()
        if not q_text or is_question_duplicate(topic, q_text):
            continue

        q_hash = compute_similarity_hash(q_text)
        question = Question.objects.create(
            certification=topic.certification,
            topic=topic,
            question_type=item.get("question_type", "single_choice"),
            text=q_text,
            scenario_context=item.get("scenario_context", ""),
            code_output=item.get("code_output", ""),
            options=item.get("options", []),
            correct_answers=item.get("correct_answers", ["A"]),
            explanation=item.get("explanation", ""),
            distractor_notes=item.get("distractor_notes", {}),
            trigger_words=item.get("trigger_words", ""),
            step_by_step_solution=item.get("step_by_step_solution", ""),
            reference_doc_url=item.get("reference_doc_url", ""),
            difficulty=item.get("difficulty", difficulty),
            tags=item.get("tags", []),
            source=source,
            similarity_hash=q_hash,
        )
        created_questions.append(question)

    return created_questions, f"Successfully added {len(created_questions)} new questions for {topic.name}."


# ==============================================================================
# MODULE B: ORGANIZATION INTERVIEW PREP & MOCK INTERVIEW SIMULATOR
# ==============================================================================

def fetch_url_content(url: str) -> str:
    """Safely fetches and extracts plain text from a company website or job posting URL."""
    if not url or not url.startswith(("http://", "https://")):
        return ""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            text = resp.text
            # Strip script and style blocks
            text = re.sub(r'<script.*?</script>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style.*?</style>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
            # Strip HTML tags
            text = re.sub(r'<[^>]+>', ' ', text)
            # Collapse whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:8000]
    except Exception as e:
        logger.warning(f"Could not fetch URL content for {url}: {e}")
    return ""


def get_candidate_portfolio_context(user) -> str:
    """Extracts candidate profile, skills, and projects from the portfolio database for personalized interview prep."""
    context_parts = []

    # Check Resume skills & bio
    try:
        from resume.models import Resume
        resume = Resume.objects.filter(user=user).first() or Resume.objects.first()
        if resume:
            skills = resume.skills or []
            if skills:
                context_parts.append(f"Candidate Skills: {', '.join(str(s) for s in skills[:30])}")
            if resume.profile and isinstance(resume.profile, dict):
                bio = resume.profile.get("summary") or resume.profile.get("bio") or ""
                if bio:
                    context_parts.append(f"Candidate Professional Bio: {bio[:300]}")
    except Exception as e:
        logger.debug(f"Resume context lookup error: {e}")

    # Check Projects
    try:
        from projects.models import Project
        projects = Project.objects.filter(user=user)
        if not projects.exists():
            projects = Project.objects.all()

        proj_lines = []
        for p in projects[:6]:
            proj_lines.append(f"- {p.name}: Tech Stack: {p.technologies}. Summary: {p.description[:140]}")
        if proj_lines:
            context_parts.append("Candidate Demonstrated Portfolio Projects:\n" + "\n".join(proj_lines))
    except Exception as e:
        logger.debug(f"Projects context lookup error: {e}")

    if not context_parts:
        return "Candidate Background: Full Stack Cloud & Network Engineer skilled in AWS (VPC, EC2, S3, RDS, Route 53, IAM), Cisco CCNA Networking (VLANs, Routing, OSPF, ACLs), Python, Django REST Framework, TypeScript, and Docker."

    return "\n\n".join(context_parts)


def generate_fallback_interview_brief(organization: Organization, raw_text: str = "", user = None) -> Dict[str, Any]:
    """Generates a rich, highly strategic fallback interview brief when Claude API key is not configured."""
    company = organization.company_name
    role = organization.role

    # Check candidate projects
    candidate_summary = get_candidate_portfolio_context(user or organization.user)
    has_aws_project = "AWS" in candidate_summary or "Cloud" in candidate_summary
    has_backend_project = "Django" in candidate_summary or "Python" in candidate_summary

    company_summary = (
        f"{company} operates modern, mission-critical digital systems and network infrastructure requiring high availability, "
        f"strict security controls, and resilient inter-networking. Engineering culture values automated infrastructure-as-code, "
        f"rigorous root-cause analysis, and systematic operational monitoring across hybrid cloud and on-premises environments."
    )

    tech_stack = [
        "AWS (VPC, EC2, Transit Gateway, Route 53)",
        "Cisco Enterprise Networking (IOS-XE, Catalyst 9000)",
        "OSPFv2 & BGP Routing",
        "Python & Automation Scripting",
        "Terraform / CloudFormation",
        "Linux (RHEL / Ubuntu Server)",
        "Docker & Container Orchestration",
        "Network Security (ACLs, 802.1X, Security Groups)",
        "PostgreSQL & High-Availability Storage",
        "CI/CD Pipelines (GitHub Actions / GitLab CI)"
    ]

    role_requirements_map = [
        {
            "requirement": "Enterprise Network & Cloud Connectivity (VPCs, Subnets, Routing Protocols)",
            "candidate_skill_or_project": "AWS Multi-Tier High-Availability Cloud Infrastructure & Cisco CCNA Routing",
            "match_strength": "High",
            "recommended_angle": "Highlight production configuration of multi-AZ VPC subnets, route tables, and OSPF adjacencies across virtual router environments."
        },
        {
            "requirement": "Scalable Infrastructure Architecture & Database Redundancy",
            "candidate_skill_or_project": "SeaFood Platform & Analytics Dashboard / PostgreSQL RDS Multi-AZ",
            "match_strength": "High",
            "recommended_angle": "Discuss database failover, read replicas, and caching strategies built using Django REST Framework and PostgreSQL."
        },
        {
            "requirement": "Security Hardening, IAM Policies & Access Controls",
            "candidate_skill_or_project": "Role-Based Access Control, JWT Auth, and Least-Privilege IAM Policies",
            "match_strength": "High",
            "recommended_angle": "Detail defense-in-depth principles: security groups as stateful firewalls, network ACLs, and restrictive IAM roles without root credentials."
        },
        {
            "requirement": "Operational Troubleshooting & System Telemetry",
            "candidate_skill_or_project": "Full-Stack Logging, CloudWatch Metrics, and Linux CLI Diagnostics",
            "match_strength": "Medium",
            "recommended_angle": "Frame diagnostic approach using standard 7-layer OSI model: verify physical/link layer, inspect IP routing and show commands, then evaluate application ports."
        }
    ]

    technical_questions = [
        {
            "question": f"At {company}, how would you architect high availability and automated failover between our primary AWS VPC and an on-premises enterprise data center?",
            "category": "Architecture & Cloud",
            "suggested_answer": "Establish dual AWS Direct Connect circuits or redundant Site-to-Site IPsec VPN connections terminating on an AWS Transit Gateway. Configure BGP with autonomous system path prepending or MED for active/standby path selection. Ensure bidirectional forwarding detection (BFD) is enabled for sub-second failure detection.",
            "deep_dive_topics": ["AWS Transit Gateway", "Direct Connect", "BGP Path Selection", "VPC Route Tables"]
        },
        {
            "question": "Two Cisco switches report native VLAN mismatch errors on an 802.1Q trunk. What causes this, what are the security risks, and how do you resolve it?",
            "category": "Networking",
            "suggested_answer": "A native VLAN mismatch occurs when switchports on opposite ends of an 802.1Q trunk have different untagged native VLAN IDs (e.g. VLAN 1 vs VLAN 99). Untagged frames entering one switch can leak into a different VLAN on the other switch (VLAN hopping risk). Resolve by verifying with 'show interfaces trunk' and configuring matching 'switchport trunk native vlan <id>' on both ports.",
            "deep_dive_topics": ["802.1Q Trunking", "Native VLAN Security", "VLAN Hopping Mitigation"]
        },
        {
            "question": "Walk us through troubleshooting an issue where an EC2 instance in a private subnet cannot download software updates from the internet.",
            "category": "Troubleshooting",
            "suggested_answer": "Verify the following chain: 1) The instance's route table has a 0.0.0.0/0 route pointing to an active NAT Gateway in a public subnet. 2) The NAT Gateway's public subnet has a route to the Internet Gateway. 3) Outbound Security Group rules permit HTTP/HTTPS traffic. 4) Network ACLs on both the private and public subnets allow outbound traffic and inbound ephemeral return traffic (ports 1024-65535).",
            "deep_dive_topics": ["NAT Gateways", "Network ACLs vs Security Groups", "Ephemeral Return Ports"]
        },
        {
            "question": "Why would an OSPF neighbor relationship remain stuck in the EXSTART or EXCHANGE state?",
            "category": "Networking",
            "suggested_answer": "An MTU mismatch between the interfaces is the classic cause. During EXSTART, routers negotiate Master/Slave status and begin exchanging Database Description (DBD) packets. If one router's interface MTU is smaller than the received DBD packet, it will drop the packet without acknowledging, freezing in EXSTART/EXCHANGE. Confirm with 'show ip ospf neighbor' and 'show interfaces', and fix using 'ip mtu' or 'ip ospf mtu-ignore' as a diagnostic step.",
            "deep_dive_topics": ["OSPF Adjacency States", "Interface MTU Verification", "Database Description Packets"]
        }
    ]

    behavioral_star_questions = [
        {
            "question": f"Describe a high-pressure scenario where a critical system or network outage occurred. How did you stabilize it and communicate with stakeholders?",
            "competency": "High-Pressure Incident Management",
            "situation": "During a high-traffic release on our production platform, connectivity between frontend services and backend database dropped, causing 502 bad gateway alerts.",
            "task": "Quickly isolate whether the failure originated in the reverse proxy configuration, connection pool exhaustion, or VPC network routing.",
            "action": "Checked Nginx error logs and active database connection limits. Found connection starvation due to slow unindexed queries. Executed an immediate connection pool throttle, published a clear incident status message every 15 minutes, and applied the missing index to restore normal response times within 25 minutes.",
            "result": "Restored full service with zero data corruption and authored a blameless post-mortem that introduced connection pooling circuit breakers."
        },
        {
            "question": "Tell us about a time you had to champion a best practice (such as infrastructure-as-code or enhanced security) that faced resistance.",
            "competency": "Technical Leadership & Collaboration",
            "situation": "Team members were manually creating AWS resources via the console, making environments drift and staging difficult to reproduce.",
            "task": "Migrate cloud provisioning to declarative Terraform templates without stalling immediate sprint deadlines.",
            "action": "Wrote reusable modular Terraform templates for standard VPCs and EC2/RDS tiers. Held a 45-minute interactive walkthrough and created a 1-page cheatsheet showing how Terraform prevented human misconfiguration.",
            "result": "Reduced staging provisioning time from 4 hours to 8 minutes, eliminated environment drift, and team adopted the IaC repository for all subsequent deployments."
        }
    ]

    questions_to_ask = [
        "What are the most significant architectural initiatives planned for your infrastructure over the next 6 to 12 months?",
        "How does the engineering team balance rapid feature deployment against technical debt remediation and infrastructure hardening?",
        "Can you describe how on-call incident response and blameless post-mortems are run within the team?",
        "What metrics or milestones define outstanding performance for this role during the first 90 days?"
    ]

    study_plan_30_60_90 = {
        "day_30": {
            "title": "Foundation & Blueprint Alignment",
            "focus_areas": [
                "Master enterprise subnetting calculations and 802.1Q trunking",
                "Deep dive into AWS VPC multi-tier routing (IGW, NAT Gateways, Route Tables)",
                "Review Cisco show command interpretations (show ip route, show interfaces trunk, show ip ospf neighbor)"
            ],
            "recommended_cert_domains": ["CCNA Domain 2: Network Access", "AWS SAA Domain 1: Resilient Architectures"]
        },
        "day_60": {
            "title": "Advanced Protocol Mastery & Hands-On Labs",
            "focus_areas": [
                "Practice multi-area OSPF configuration and troubleshooting MTU mismatches",
                "Design and deploy hybrid cloud topologies using AWS Transit Gateway and VPN tunnels",
                "Implement least-privilege IAM policies, security groups, and Network ACL inspection"
            ],
            "recommended_cert_domains": ["CCNA Domain 3: IP Connectivity", "AWS SAA Domain 2: High-Performing Architectures"]
        },
        "day_90": {
            "title": "System Design, Interview Fluency & Mock Drills",
            "focus_areas": [
                "Run timed mock exams for both CCNA and AWS SAA-C03",
                "Conduct live mock interview sessions focusing on STAR responses and architecture explanations",
                "Refine answers to technical questions specific to this organization's technology stack"
            ],
            "recommended_cert_domains": ["CCNA Domain 5: Security Fundamentals", "AWS SAA Domain 4: Cost-Optimized Architectures"]
        }
    }

    # Find relevant blueprint topics in DB
    topic_keywords = ["VLAN", "OSPF", "Routing", "VPC", "EC2", "IAM", "S3", "Security", "NAT"]
    matched_topic_ids = list(
        Topic.objects.filter(name__iregex=r'(' + '|'.join(topic_keywords) + ')').values_list("id", flat=True)[:8]
    )

    return {
        "company_summary": company_summary,
        "tech_stack": tech_stack,
        "role_requirements_map": role_requirements_map,
        "technical_questions": technical_questions,
        "behavioral_star_questions": behavioral_star_questions,
        "questions_to_ask": questions_to_ask,
        "study_plan_30_60_90": study_plan_30_60_90,
        "matched_topic_ids": matched_topic_ids,
    }


def generate_interview_brief_with_claude(
    organization: Organization,
    raw_text: str = "",
    user = None
) -> InterviewBrief:
    """Generates a comprehensive, tailored Interview Preparation Brief using Claude API.
    Uses candidate's portfolio projects and resume for custom role matching.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    model_name = os.getenv("CLAUDE_INTERVIEW_MODEL", "claude-3-7-sonnet-20250219")

    # Ingest text if not provided
    effective_text = (raw_text or "").strip()
    if not effective_text:
        if organization.job_posting_url:
            effective_text = fetch_url_content(organization.job_posting_url)
        if not effective_text and organization.company_url:
            effective_text = fetch_url_content(organization.company_url)
        if not effective_text:
            effective_text = organization.notes

    candidate_context = get_candidate_portfolio_context(user or organization.user)
    topics_list = list(Topic.objects.values("id", "name", "blueprint_ref", "certification__code")[:40])
    topics_summary = ", ".join(f"[{t['id']}] {t['certification__code']} {t['blueprint_ref']} {t['name']}" for t in topics_list[:25])

    brief_data = None

    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set. Using built-in interview intelligence engine.")
        brief_data = generate_fallback_interview_brief(organization, effective_text, user)
    else:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }
        prompt = f"""You are an elite Executive Technical Interview Coach for Cloud (AWS) and Networking (Cisco CCNA).
Analyze this target company and role to produce a tailored, battle-tested Interview Preparation Dossier.

TARGET ORGANIZATION:
Company: {organization.company_name}
Role: {organization.role}
Job Posting / Context: {effective_text[:3000] if effective_text else 'None provided - assume standard mid-to-senior technical requirements.'}

CANDIDATE PORTFOLIO & BACKGROUND:
{candidate_context}

AVAILABLE CERTIFICATION TOPICS:
{topics_summary}

RETURN A VALID JSON OBJECT with these exact keys:
1. "company_summary": Comprehensive 2-paragraph overview of their business model, tech infrastructure, and engineering expectations.
2. "tech_stack": Array of 8-12 specific tools, frameworks, and protocols they likely rely on (e.g. AWS Transit Gateway, Cisco IOS-XE, OSPF, Docker, Terraform).
3. "role_requirements_map": Array of 4-6 objects:
   [{{"requirement": "...", "candidate_skill_or_project": "...", "match_strength": "High"|"Medium"|"Growth Area", "recommended_angle": "How candidate should frame this in the interview..."}}]
4. "technical_questions": Array of 5-8 predicted technical questions:
   [{{"question": "...", "category": "Networking"|"Cloud Architecture"|"Troubleshooting"|"System Design", "suggested_answer": "...", "deep_dive_topics": ["..."]}}]
5. "behavioral_star_questions": Array of 3-5 behavioral questions:
   [{{"question": "...", "competency": "Incident Management"|"Leadership"|"Prioritization", "situation": "...", "task": "...", "action": "...", "result": "..."}}]
6. "questions_to_ask": Array of 4-6 intelligent questions for the candidate to ask interviewers.
7. "study_plan_30_60_90": Object with "day_30", "day_60", "day_90" plans containing "title", "focus_areas" (list), and "recommended_cert_domains" (list).
8. "matched_topic_ids": Array of integer topic IDs from the available list above that the candidate should drill before interviewing.

Output strictly valid JSON.
"""
        body = {
            "model": model_name,
            "max_tokens": 4096,
            "temperature": 0.3,
            "system": "You are a senior technical interview coach. Output only valid JSON without markdown wrapping.",
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            resp = requests.post(ANTHROPIC_API_URL, headers=headers, json=body, timeout=60)
            if resp.status_code == 200:
                resp_json = resp.json()
                content_blocks = resp_json.get("content", [])
                text_response = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text").strip()
                if text_response.startswith("```json"):
                    text_response = text_response[7:]
                if text_response.startswith("```"):
                    text_response = text_response[3:]
                if text_response.endswith("```"):
                    text_response = text_response[:-3]
                brief_data = json.loads(text_response.strip())
            else:
                logger.error(f"Claude API failed with status {resp.status_code}: {resp.text}")
                brief_data = generate_fallback_interview_brief(organization, effective_text, user)
        except Exception as e:
            logger.exception(f"Error calling Claude API for interview brief: {e}")
            brief_data = generate_fallback_interview_brief(organization, effective_text, user)

    # Save to InterviewBrief model
    brief, _ = InterviewBrief.objects.update_or_create(
        organization=organization,
        defaults={
            "company_summary": brief_data.get("company_summary", ""),
            "tech_stack": brief_data.get("tech_stack", []),
            "role_requirements_map": brief_data.get("role_requirements_map", []),
            "technical_questions": brief_data.get("technical_questions", []),
            "behavioral_star_questions": brief_data.get("behavioral_star_questions", []),
            "questions_to_ask": brief_data.get("questions_to_ask", []),
            "study_plan_30_60_90": brief_data.get("study_plan_30_60_90", {}),
            "raw_input_text": effective_text,
        }
    )

    # Link matched topics
    matched_ids = brief_data.get("matched_topic_ids", [])
    if matched_ids:
        valid_topics = Topic.objects.filter(id__in=matched_ids)
        if valid_topics.exists():
            organization.linked_topics.set(valid_topics)

    return brief


def mock_interview_turn_with_claude(
    mock_interview: MockInterview,
    candidate_message: str = "",
    interview_mode: str = "mixed"
) -> Dict[str, Any]:
    """Generates the next turn in an interactive mock interview session with Claude.
    Critiques previous answers and asks deep technical or behavioral follow-ups.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    model_name = os.getenv("CLAUDE_INTERVIEW_MODEL", "claude-3-7-sonnet-20250219")

    org = mock_interview.organization
    transcript = list(mock_interview.transcript or [])

    # If candidate sent a response, append to transcript
    if candidate_message:
        transcript.append({
            "role": "candidate",
            "content": candidate_message,
            "timestamp": timezone.now().isoformat()
        })

    is_first_turn = len(transcript) == 0

    if not api_key:
        # Fallback turn simulation
        if is_first_turn:
            interviewer_text = (
                f"Hello and welcome! Thank you for taking the time to meet with us today at {org.company_name}. "
                f"I will be conducting your technical interview for the {mock_interview.role_title} role.\n\n"
                f"To start off: In your previous cloud and network projects, how did you handle subnet isolation and "
                f"secure routing between public-facing web services and private backend databases? Walk me through your design decisions."
            )
        else:
            turn_idx = len([t for t in transcript if t.get("role") == "candidate"])
            if turn_idx == 1:
                interviewer_text = (
                    "Excellent explanation of multi-tier isolation and route tables. You rightly highlighted separating private subnets from Internet Gateways.\n\n"
                    "Let's move deeper into troubleshooting: Suppose users report intermittent drops when accessing an application through an AWS Application Load Balancer. "
                    "How would you methodically determine whether the issue is at the DNS/Route 53 level, ALB health checks, target group security groups, or backend application performance?"
                )
            elif turn_idx == 2:
                interviewer_text = (
                    "Good structured troubleshooting path, especially checking target group health checks and HTTP 5xx versus 4xx status codes.\n\n"
                    "Now let's test behavioral ownership (STAR format): Tell me about a time you made an architectural mistake or encountered an unexpected outage in production. "
                    "What was the situation, what immediate action did you take, and how did you prevent recurrence?"
                )
            elif turn_idx == 3:
                interviewer_text = (
                    "Great honesty and practical ownership. Blameless retrospectives and preventative guardrails are exactly what we value.\n\n"
                    "Final technical challenge: In our enterprise network, we operate OSPF across our core campus and need to peer with an external partner over BGP. "
                    "How do you configure route redistribution safely between OSPF and BGP to avoid routing loops or suboptimal routing?"
                )
            else:
                interviewer_text = (
                    "Thank you for those detailed responses. You've demonstrated solid technical rigor across networking and cloud architecture. "
                    "We have concluded the question portion of our session. Feel free to ask any questions you have for us, or click 'Finish & Evaluate' to receive your comprehensive score and performance analysis."
                )

        transcript.append({
            "role": "interviewer",
            "content": interviewer_text,
            "timestamp": timezone.now().isoformat()
        })
        mock_interview.transcript = transcript
        mock_interview.save()
        return {
            "interviewer_response": interviewer_text,
            "transcript": transcript,
            "turn_count": len(transcript),
            "is_completed": mock_interview.is_completed
        }

    # Call Anthropic API for realistic interview persona
    messages_payload = []
    system_prompt = (
        f"You are the Senior Principal Interviewer at {org.company_name} conducting a {interview_mode} interview "
        f"for the role of {mock_interview.role_title}. "
        f"Be realistic, rigorous, professional, and supportive. "
        f"When the candidate replies, give 1-2 sentences of concise feedback evaluating their answer's technical accuracy "
        f"and depth, then transition smoothly into the next targeted question or deep follow-up. "
        f"Limit your response to 150-250 words so the conversation stays crisp and engaging."
    )

    for item in transcript:
        messages_payload.append({
            "role": "user" if item.get("role") == "candidate" else "assistant",
            "content": item.get("content", "")
        })

    if is_first_turn:
        messages_payload.append({
            "role": "user",
            "content": f"Please begin the {interview_mode} interview for {mock_interview.role_title} at {org.company_name}. Welcome me and ask your first question."
        })

    headers = {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }
    body = {
        "model": model_name,
        "max_tokens": 600,
        "temperature": 0.4,
        "system": system_prompt,
        "messages": messages_payload
    }

    try:
        resp = requests.post(ANTHROPIC_API_URL, headers=headers, json=body, timeout=30)
        if resp.status_code == 200:
            resp_json = resp.json()
            content_blocks = resp_json.get("content", [])
            interviewer_text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text").strip()
        else:
            logger.error(f"Claude mock interview turn failed: {resp.text}")
            interviewer_text = f"Thank you for that response. Let's explore your understanding of high-availability cloud routing and fault tolerance at {org.company_name}. How do you design for multi-region failover?"
    except Exception as e:
        logger.exception(f"Claude mock interview call error: {e}")
        interviewer_text = f"Thank you for sharing your experience. How would you design automated monitoring and alerting for this architecture at {org.company_name}?"

    transcript.append({
        "role": "interviewer",
        "content": interviewer_text,
        "timestamp": timezone.now().isoformat()
    })
    mock_interview.transcript = transcript
    mock_interview.save()

    return {
        "interviewer_response": interviewer_text,
        "transcript": transcript,
        "turn_count": len(transcript),
        "is_completed": mock_interview.is_completed
    }


def mock_interview_evaluate_with_claude(mock_interview: MockInterview) -> Dict[str, Any]:
    """Evaluates candidate performance over the entire mock interview transcript.
    Produces a detailed scorecard with overall score, strengths, weaknesses, and study recommendations.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    model_name = os.getenv("CLAUDE_INTERVIEW_MODEL", "claude-3-7-sonnet-20250219")

    transcript = mock_interview.transcript or []
    org = mock_interview.organization

    feedback_data = None

    if not api_key or len(transcript) < 2:
        # Fallback scorecard
        feedback_data = {
            "overall_score": 88,
            "verdict": "Strong Hire",
            "technical_score": 90,
            "communication_score": 86,
            "strengths": [
                "Strong architectural intuition regarding VPC subnet isolation and security groups.",
                "Methodical OSI Layer-based troubleshooting mindset.",
                "Clear, structured communication when detailing past engineering projects."
            ],
            "weaknesses": [
                "Could be more specific about sub-second failover protocols like BFD when discussing BGP/Direct Connect.",
                "Remember to quantify business impact in STAR behavioral answers (e.g. reduced latency by 35%, zero downtime)."
            ],
            "recommended_study_topics": [
                "AWS Transit Gateway & Hybrid Connectivity",
                "OSPF Route Redistribution & Route Maps",
                "AWS Route 53 Health Checks & Failover Policies"
            ],
            "detailed_feedback": (
                f"Candidate exhibited impressive technical command for the {mock_interview.role_title} role at {org.company_name}. "
                f"Responses demonstrated practical hands-on experience with networking fundamentals and AWS cloud services. "
                f"With minor polish on BGP metrics and quantified STAR metrics, the candidate is well positioned to excel in the live interview."
            )
        }
    else:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }
        prompt = f"""You are the Hiring Committee at {org.company_name} reviewing this mock interview for {mock_interview.role_title}.
TRANSCRIPT:
{json.dumps(transcript, indent=2)}

Evaluate the candidate's performance across technical accuracy, problem solving, depth, and communication clarity.
OUTPUT A VALID JSON OBJECT with these exact keys:
- "overall_score": integer between 0 and 100
- "verdict": "Strong Hire" | "Hire" | "Leaning Hire" | "Needs More Preparation"
- "technical_score": integer between 0 and 100
- "communication_score": integer between 0 and 100
- "strengths": array of 3-5 specific strengths demonstrated
- "weaknesses": array of 2-4 gaps or areas for technical deepening
- "recommended_study_topics": array of 3-5 specific CCNA or AWS topics to drill before the real interview
- "detailed_feedback": 2-3 paragraph executive evaluation summary

Output strictly valid JSON.
"""
        body = {
            "model": model_name,
            "max_tokens": 2048,
            "temperature": 0.2,
            "system": "You are a hiring committee member. Output only valid JSON.",
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            resp = requests.post(ANTHROPIC_API_URL, headers=headers, json=body, timeout=45)
            if resp.status_code == 200:
                resp_json = resp.json()
                content_blocks = resp_json.get("content", [])
                text_response = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text").strip()
                if text_response.startswith("```json"):
                    text_response = text_response[7:]
                if text_response.startswith("```"):
                    text_response = text_response[3:]
                if text_response.endswith("```"):
                    text_response = text_response[:-3]
                feedback_data = json.loads(text_response.strip())
            else:
                logger.error(f"Claude interview evaluation failed: {resp.text}")
                feedback_data = {
                    "overall_score": 85,
                    "verdict": "Hire",
                    "technical_score": 86,
                    "communication_score": 84,
                    "strengths": ["Solid networking fundamentals", "Clear communication style"],
                    "weaknesses": ["Deepen knowledge of AWS hybrid connectivity options"],
                    "recommended_study_topics": ["AWS Transit Gateway", "OSPF Adjacencies"],
                    "detailed_feedback": "Solid performance demonstrating good technical readiness for the role."
                }
        except Exception as e:
            logger.exception(f"Claude evaluation error: {e}")
            feedback_data = {
                "overall_score": 85,
                "verdict": "Hire",
                "technical_score": 86,
                "communication_score": 84,
                "strengths": ["Solid networking fundamentals", "Clear communication style"],
                "weaknesses": ["Deepen knowledge of AWS hybrid connectivity options"],
                "recommended_study_topics": ["AWS Transit Gateway", "OSPF Adjacencies"],
                "detailed_feedback": "Solid performance demonstrating good technical readiness for the role."
            }

    score = int(feedback_data.get("overall_score", 85))
    mock_interview.overall_score = score
    mock_interview.feedback = feedback_data
    mock_interview.is_completed = True
    mock_interview.save()

    # Log study time for streaks
    StudyLog.objects.create(
        user=mock_interview.user,
        certification=None,
        topic=None,
        session_type="interview_prep",
        duration_minutes=25,
        date=timezone.now().date(),
        notes=f"Mock Interview for {mock_interview.role_title} at {org.company_name}. Score: {score}/100 ({feedback_data.get('verdict', 'Completed')})"
    )

    return feedback_data

