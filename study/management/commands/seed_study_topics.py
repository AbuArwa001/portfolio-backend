from django.core.management.base import BaseCommand
from django.utils.text import slugify
from study.models import StudyCertification, Topic, Lab


class Command(BaseCommand):
    help = "Seeds official Cisco CCNA 200-301 and AWS SAA-C03 blueprint topics and foundational labs"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding Study Certifications & Topics..."))

        # 1. Cisco CCNA 200-301
        ccna, _ = StudyCertification.objects.update_or_create(
            code="CCNA-200-301",
            defaults={
                "name": "Cisco Certified Network Associate",
                "vendor": "Cisco",
                "exam_code": "200-301",
                "description": "Validates foundational networking knowledge across network access, IP connectivity, IP services, security fundamentals, and automation.",
                "icon": "Network",
                "total_exam_time_minutes": 120,
                "total_exam_questions": 100,
                "passing_score_pct": 82,
                "is_active": True,
            }
        )

        ccna_topics = [
            # Domain 1: Network Fundamentals (20%)
            (1, "Network Fundamentals", 20, "1.1", "Network Devices & Roles", "Routers, Layer 2 & 3 switches, next-gen firewalls, wireless access points, wireless LAN controllers, and endpoints.", "Router"),
            (1, "Network Fundamentals", 20, "1.2", "Network Topology Architectures", "Two-tier, three-tier, spine-leaf, WAN, SOHO, on-premises vs cloud architectures.", "Network"),
            (1, "Network Fundamentals", 20, "1.3", "Physical Cabling & Interface Properties", "Single-mode and multimode fiber, copper twisted-pair cabling, Power over Ethernet (PoE/PoE+), cable speeds and distance limits.", "Cable"),
            (1, "Network Fundamentals", 20, "1.4", "Interface & Cable Troubleshooting", "Collisions, runts, giants, input/output errors, CRC errors, duplex mismatch, speed autonegotiation.", "AlertTriangle"),
            (1, "Network Fundamentals", 20, "1.5", "TCP vs UDP Comparison", "Connection-oriented vs connectionless, sequencing, acknowledgements, flow control, common well-known ports.", "ArrowLeftRight"),
            (1, "Network Fundamentals", 20, "1.6", "IPv4 Subnetting & VLSM", "Subnetting calculations, magic number technique, prefix lengths (/8 to /30), usable host ranges, broadcast addresses, VLSM allocation.", "Binary"),
            (1, "Network Fundamentals", 20, "1.7", "Private IPv4 & RFC 1918", "Private address spaces 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, loopback 127.0.0.0/8, link-local APIPA 169.254.0.0/16.", "ShieldCheck"),
            (1, "Network Fundamentals", 20, "1.8", "IPv6 Addressing & Configuration", "Global unicast, unique local, link-local (fe80::), modified EUI-64, SLAAC, multicast, solicited-node multicast.", "Cpu"),
            (1, "Network Fundamentals", 20, "1.9", "Wireless Principles & RF", "2.4 GHz vs 5 GHz vs 6 GHz bands, non-overlapping channels (1, 6, 11), SSID, BSSID, RF interference, basic wireless topologies.", "Wifi"),
            (1, "Network Fundamentals", 20, "1.10", "Virtualization Fundamentals", "Server virtualization, Type 1 vs Type 2 hypervisors, virtual machines, virtual switches, vNICs.", "Boxes"),

            # Domain 2: Network Access (20%)
            (2, "Network Access", 20, "2.1", "VLANs & Segmentation", "VLAN creation, access ports, data VLAN, voice VLAN with QoS, management VLAN, default VLAN 1 security considerations.", "Layers"),
            (2, "Network Access", 20, "2.2", "802.1Q Trunking & Native VLAN", "Trunk configuration, 802.1Q encapsulation tagging, native VLAN untagged traffic, native VLAN mismatch security vulnerabilities.", "Split"),
            (2, "Network Access", 20, "2.3", "Discovery Protocols (CDP & LLDP)", "Cisco Discovery Protocol (CDP) and Link Layer Discovery Protocol (LLDP) configuration, TLVs, security best practices.", "Search"),
            (2, "Network Access", 20, "2.4", "EtherChannel (LACP & PAgP)", "Port aggregation benefits, LACP (active/passive), PAgP (desirable/auto), static on mode, bundle prerequisites, load balancing methods.", "GitMerge"),
            (2, "Network Access", 20, "2.5", "Spanning Tree Protocol (STP & RSTP)", "Loop prevention, 802.1D vs 802.1w (RSTP), root bridge election, bridge priority, path cost, port roles (Root, Designated, Alternate, Backup), port states.", "Activity"),
            (2, "Network Access", 20, "2.6", "STP Enhancements (PortFast & BPDU Guard)", "Edge port optimization with PortFast, protecting topology with BPDU Guard, Root Guard, Loop Guard.", "ShieldAlert"),
            (2, "Network Access", 20, "2.7", "Cisco Wireless Architectures", "Autonomous AP vs Split-MAC architecture, Lightweight AP (LAP) modes (Local, FlexConnect, Sniffer, Monitor, Rogue Detector), CAPWAP tunnel.", "Radio"),
            (2, "Network Access", 20, "2.8", "WLAN Configuration on Cisco WLC", "WLC GUI navigation, creating WLANs, dynamic interface mapping, security profiles (WPA2/WPA3 PSK, 802.1X Enterprise).", "Sliders"),

            # Domain 3: IP Connectivity (25%)
            (3, "IP Connectivity", 25, "3.1", "Routing Table Components & Forwarding", "Routing codes (C, S, O, D), network prefix, subnet mask, administrative distance, metric, next-hop IP, outgoing interface, gateway of last resort.", "ListOrdered"),
            (3, "IP Connectivity", 25, "3.2", "Routing Logic & Longest Match", "Longest prefix match rule, administrative distance hierarchy, metric comparison, routing decision engine.", "Compass"),
            (3, "IP Connectivity", 25, "3.3", "IPv4 & IPv6 Static Routing", "Standard static routes, default routes (0.0.0.0/0, ::/0), host routes (/32, /128), floating static routes for backup with higher AD.", "Navigation"),
            (3, "IP Connectivity", 25, "3.4", "Single-Area OSPFv2 Fundamentals", "Link-state operation, LSA types (Type 1, Type 2), cost metric calculation (reference bandwidth), area 0 backbone.", "Share2"),
            (3, "IP Connectivity", 25, "3.5", "OSPFv2 Adjacencies & Network Types", "OSPF neighbor states (Down, Init, 2-Way, ExStart, Exchange, Loading, Full), broadcast DR/BDR election, point-to-point network type.", "RadioReceiver"),
            (3, "IP Connectivity", 25, "3.6", "OSPFv2 Configuration & Tuning", "router ospf process, network statement vs interface ospf, passive-interface, router-id, hello/dead timers matching.", "Settings"),
            (3, "IP Connectivity", 25, "3.7", "First Hop Redundancy (HSRP)", "HSRP v1 vs v2, active and standby router roles, virtual MAC address format, priority and preemption, tracking interfaces.", "Shuffle"),

            # Domain 4: IP Services (10%)
            (4, "IP Services", 10, "4.1", "Inside Source NAT & PAT", "Static NAT (1-to-1), dynamic NAT (pool), Port Address Translation (PAT / overload), ip nat inside/outside commands, show ip nat translations.", "Repeat"),
            (4, "IP Services", 10, "4.2", "NTP Operation", "Network Time Protocol client/server configuration, stratum levels (1 to 15), ntp server command, verifying clock synchronization.", "Clock"),
            (4, "IP Services", 10, "4.3", "DHCP Server & Relay Agent", "DHCP DORA process, Cisco IOS DHCP pool, network, default-router, dns-server, excluded-addresses, ip helper-address relay agent.", "Server"),
            (4, "IP Services", 10, "4.4", "DNS Resolution", "ip domain-lookup, ip name-server, resolving hostnames to IP addresses, testing with nslookup and ping.", "Globe"),
            (4, "IP Services", 10, "4.5", "SNMP v2c & v3", "Simple Network Management Protocol MIB, OID hierarchy, SNMP traps vs informs, SNMP v2c community strings vs SNMP v3 authentication & encryption.", "HardDrive"),
            (4, "IP Services", 10, "4.6", "Syslog & Logging Levels", "Syslog logging levels 0 (emergencies) through 7 (debugging), logging console, logging buffered, logging host.", "Terminal"),
            (4, "IP Services", 10, "4.7", "Per-Hop Behavior QoS", "Quality of Service concepts: classification, marking (CoS L2, DSCP L3), queuing (FIFO, CBWFQ, LLQ), congestion avoidance (WRED), traffic shaping vs policing.", "BarChart2"),
            (4, "IP Services", 10, "4.8", "SSH vs Telnet Secure Remote Access", "Crypto key generation (rsa), vty line configuration, transport input ssh, privilege levels, username/secret authentication.", "Lock"),

            # Domain 5: Security Fundamentals (15%)
            (5, "Security Fundamentals", 15, "5.1", "Security Concepts & Attack Vectors", "Threats, vulnerabilities, exploits, reconnaissance attacks, access attacks, DoS/DDoS attacks, social engineering.", "Shield"),
            (5, "Security Fundamentals", 15, "5.2", "Device Access & AAA with TACACS+/RADIUS", "Local user database vs centralized AAA, authentication, authorization, accounting, TACACS+ (TCP 49, encrypts entire packet) vs RADIUS (UDP, encrypts password only).", "Key"),
            (5, "Security Fundamentals", 15, "5.3", "Standard IPv4 ACLs", "Numbered (1-99, 1300-1999) and named standard ACLs, source IP filtering, implicit deny all, placement nearest destination.", "Filter"),
            (5, "Security Fundamentals", 15, "5.4", "Extended IPv4 ACLs", "Numbered (100-199, 2000-2699) and named extended ACLs, protocol (ip, tcp, udp, icmp), source/dest IP and port matching, established keyword, placement nearest source.", "SlidersHorizontal"),
            (5, "Security Fundamentals", 15, "5.5", "Layer 2 Security (Port Security)", "switchport port-security, static, dynamic, sticky MAC addresses, maximum count, violation modes (protect, restrict, shutdown), err-disabled recovery.", "Anchor"),
            (5, "Security Fundamentals", 15, "5.6", "DHCP Snooping & Dynamic ARP Inspection", "DHCP snooping trusted vs untrusted ports, snooping binding database, DAI validation of ARP requests/replies against snooping table.", "ShieldCheck"),
            (5, "Security Fundamentals", 15, "5.7", "Wireless Security Protocols", "WEP (legacy), WPA/WPA2 Personal (PSK) and Enterprise (802.1X), WPA3 SAE (Simultaneous Authentication of Equals), Protected Management Frames (PMF).", "WifiOff"),
            (5, "Security Fundamentals", 15, "5.8", "VPN Architectures (IPsec & SSL/TLS)", "Site-to-site IPsec VPNs, remote access VPNs, IPsec protocols: Authentication Header (AH) vs Encapsulating Security Payload (ESP), IKE phases.", "Fingerprint"),

            # Domain 6: Automation & Programmability (10%)
            (6, "Automation & Programmability", 10, "6.1", "Controller-Based vs Traditional Networking", "Management plane, control plane, data plane separation, centralized control vs distributed protocols, Cisco DNA Center / Catalyst Center.", "Network"),
            (6, "Automation & Programmability", 10, "6.2", "Software-Defined Architecture (Overlay & Underlay)", "Fabric architecture, underlay network (physical devices, IP routing), overlay network (VXLAN encapsulation, virtual tunnels), Cisco SD-Access and SD-WAN.", "CloudRain"),
            (6, "Automation & Programmability", 10, "6.3", "REST APIs & HTTP Verbs", "Representational State Transfer principles, URI structure, HTTP verbs (GET, POST, PUT, PATCH, DELETE), status codes (200, 201, 400, 401, 403, 404, 500).", "Code"),
            (6, "Automation & Programmability", 10, "6.4", "Data Formats (JSON, XML, YAML)", "JSON object, array, key-value pairs, formatting conventions, comparing JSON, XML, and YAML in network programmability.", "FileCode"),
            (6, "Automation & Programmability", 10, "6.5", "Configuration Management Tools", "Ansible (agentless, SSH, YAML playbooks, push model), Puppet (agent-based, Ruby/declarative, pull model), Chef (agent-based, Ruby recipes, pull model), Terraform infrastructure-as-code.", "Cpu"),
        ]

        for order, (d_num, d_name, d_wt, bp_ref, name, desc, icon) in enumerate(ccna_topics, start=1):
            slug = slugify(f"{bp_ref}-{name}")
            Topic.objects.update_or_create(
                certification=ccna,
                slug=slug,
                defaults={
                    "domain_number": d_num,
                    "domain_name": d_name,
                    "domain_weight_pct": d_wt,
                    "blueprint_ref": bp_ref,
                    "name": name,
                    "order": order,
                    "description": desc,
                    "icon": icon,
                }
            )

        # 2. AWS Solutions Architect Associate SAA-C03
        aws_saa, _ = StudyCertification.objects.update_or_create(
            code="AWS-SAA-C03",
            defaults={
                "name": "AWS Certified Solutions Architect - Associate",
                "vendor": "AWS",
                "exam_code": "SAA-C03",
                "description": "Validates ability to design secure, resilient, high-performing, and cost-optimized distributed architectures on Amazon Web Services.",
                "icon": "Cloud",
                "total_exam_time_minutes": 130,
                "total_exam_questions": 65,
                "passing_score_pct": 72,
                "is_active": True,
            }
        )

        aws_topics = [
            # Domain 1: Design Secure Architectures (30%)
            (1, "Design Secure Architectures", 30, "1.1", "AWS Identity & Access Management (IAM)", "IAM users, groups, roles, policy structure (Effect, Principal, Action, Resource, Condition), permission boundaries, Service Control Policies (SCPs) in AWS Organizations.", "Key"),
            (1, "Design Secure Architectures", 30, "1.2", "Secure VPC Architecture & Segmentation", "VPC design with CIDR blocks, public vs private subnets, Internet Gateways, NAT Gateways vs NAT Instances, Route tables.", "Network"),
            (1, "Design Secure Architectures", 30, "1.3", "Security Groups & Network ACLs", "Security Groups (stateful, allow rules only, instance level) vs Network ACLs (stateless, allow & deny rules, numbered evaluation, subnet level).", "ShieldCheck"),
            (1, "Design Secure Architectures", 30, "1.4", "VPC Connectivity (Peering, Transit Gateway & Endpoints)", "VPC Peering (non-transitive), AWS Transit Gateway hub-and-spoke, VPC Endpoints: Gateway Endpoints (S3, DynamoDB) vs Interface Endpoints (AWS PrivateLink).", "GitMerge"),
            (1, "Design Secure Architectures", 30, "1.5", "Data Encryption with AWS KMS & Secrets Manager", "AWS KMS Customer Managed Keys (CMK), AWS managed keys, envelope encryption, key policies, AWS Secrets Manager automatic rotation, AWS Certificate Manager (ACM).", "Lock"),
            (1, "Design Secure Architectures", 30, "1.6", "Edge & Application Security (WAF, Shield & CloudFront)", "AWS WAF managed rule groups and rate limiting, AWS Shield Standard vs Advanced DDoS protection, CloudFront signed URLs, signed cookies, Origin Access Control (OAC).", "ShieldAlert"),

            # Domain 2: Design Resilient Architectures (26%)
            (2, "Design Resilient Architectures", 26, "2.1", "High Availability Compute (EC2, ASG & ELB)", "Multi-AZ Auto Scaling Groups, Launch Templates, health check types (EC2 vs ELB), Application Load Balancer (ALB) path-based routing vs Network Load Balancer (NLB) ultra-low latency.", "Boxes"),
            (2, "Design Resilient Architectures", 26, "2.2", "Resilient S3 Storage & Disaster Recovery", "Amazon S3 Cross-Region Replication (CRR) and Same-Region Replication (SRR), S3 Versioning, S3 Object Lock (Compliance vs Governance mode), S3 lifecycle transitions.", "HardDrive"),
            (2, "Design Resilient Architectures", 26, "2.3", "Multi-AZ Relational Databases (RDS & Aurora)", "Amazon RDS Multi-AZ synchronous standby replica for high availability vs asynchronous Read Replicas for read scaling, Aurora Multi-Master, Aurora Global Database cross-region DR.", "Database"),
            (2, "Design Resilient Architectures", 26, "2.4", "Route 53 Routing Policies & DNS Failover", "Simple, Weighted, Latency-based, Failover (active-passive with health checks), Geolocation, Geoproximity (Traffic Flow), and Multi-Value Answer routing policies.", "Globe"),
            (2, "Design Resilient Architectures", 26, "2.5", "Disaster Recovery Strategies (RPO & RTO)", "Comparing DR strategies: Backup & Restore (high RTO/RPO, lowest cost), Pilot Light, Warm Standby, and Multi-Site Active-Active (near-zero RTO/RPO, highest cost).", "RefreshCcw"),

            # Domain 3: Design High-Performing Architectures (24%)
            (3, "Design High-Performing Architectures", 24, "3.1", "Compute Sizing & Storage Performance (EBS, EFS & FSx)", "EC2 instance types (General Purpose, Compute, Memory, Storage Optimized), EBS gp3 vs io2 Block Express, Instance Store (ephemeral, high IOPS), EFS Multi-AZ file system, FSx for Lustre / Windows.", "Server"),
            (3, "Design High-Performing Architectures", 24, "3.2", "Caching with ElastiCache & DynamoDB Accelerator (DAX)", "Amazon ElastiCache Redis (in-memory data structure, cluster mode, replication) vs Memcached (multithreaded simple caching), DynamoDB DAX microsecond in-memory cache.", "Zap"),
            (3, "Design High-Performing Architectures", 24, "3.3", "Content Delivery with CloudFront & Global Accelerator", "Amazon CloudFront caching, TTL, invalidation costs, Lambda@Edge and CloudFront Functions, AWS Global Accelerator anycast IP and TCP/UDP acceleration.", "Radio"),
            (3, "Design High-Performing Architectures", 24, "3.4", "Decoupling with SQS, SNS & EventBridge", "Amazon SQS Standard (unlimited throughput, at-least-once) vs FIFO (strict ordering, exactly-once), DLQs, Amazon SNS pub/sub fanout pattern, Amazon EventBridge schema registry and SaaS integrations.", "Layers"),
            (3, "Design High-Performing Architectures", 24, "3.5", "Serverless Architectures (Lambda, API Gateway & Step Functions)", "AWS Lambda concurrency limits, provisioned concurrency, execution timeout, Amazon API Gateway REST vs HTTP APIs, throttling, AWS Step Functions standard vs express workflows.", "Cpu"),

            # Domain 4: Design Cost-Optimized Architectures (20%)
            (4, "Design Cost-Optimized Architectures", 20, "4.1", "S3 Storage Classes & Cost Optimization", "S3 Standard, S3 Standard-IA, S3 One Zone-IA, S3 Glacier Instant Retrieval, Flexible Retrieval, Deep Archive, S3 Intelligent-Tiering automatic cost savings.", "PiggyBank"),
            (4, "Design Cost-Optimized Architectures", 20, "4.2", "EC2 Pricing Models & Compute Purchasing", "On-Demand vs Compute Savings Plans vs EC2 Instance Savings Plans vs Standard/Convertible Reserved Instances vs Spot Instances (up to 90% discount for fault-tolerant workloads).", "DollarSign"),
            (4, "Design Cost-Optimized Architectures", 20, "4.3", "Database & Serverless Cost Optimization", "Amazon Aurora Serverless v2 scaling ACUs, RDS stop/start, DynamoDB On-Demand capacity for unpredictable workloads vs Provisioned capacity with Auto Scaling.", "TrendingDown"),
            (4, "Design Cost-Optimized Architectures", 20, "4.4", "AWS Cost Governance, Budgets & Cost Explorer", "AWS Cost Explorer reports, AWS Budgets alerts (forecasted vs actual), Cost Allocation Tags, AWS Compute Optimizer recommendations.", "PieChart"),
            (4, "Design Cost-Optimized Architectures", 20, "4.5", "Network Data Transfer Cost Optimization", "Minimizing data transfer costs: Inter-AZ vs Inter-Region vs Internet out, using VPC Gateway Endpoints to eliminate NAT Gateway data processing charges.", "ArrowDownUp"),
        ]

        for order, (d_num, d_name, d_wt, bp_ref, name, desc, icon) in enumerate(aws_topics, start=1):
            slug = slugify(f"{bp_ref}-{name}")
            Topic.objects.update_or_create(
                certification=aws_saa,
                slug=slug,
                defaults={
                    "domain_number": d_num,
                    "domain_name": d_name,
                    "domain_weight_pct": d_wt,
                    "blueprint_ref": bp_ref,
                    "name": name,
                    "order": order,
                    "description": desc,
                    "icon": icon,
                }
            )

        # 3. Seed initial starter Labs with complete topologies, tasks, hints, and expected config checker rules
        self.stdout.write(self.style.NOTICE("Seeding foundational CCNA and AWS Labs..."))

        # CCNA Lab 1: VLANs & 802.1Q Trunking
        vlan_topic = Topic.objects.filter(certification=ccna, blueprint_ref="2.1").first()
        if vlan_topic:
            Lab.objects.update_or_create(
                topic=vlan_topic,
                slug="lab-ccna-vlan-trunking-basic",
                defaults={
                    "title": "Configuring VLANs, Access Ports, and 802.1Q Trunking",
                    "difficulty": "beginner",
                    "estimated_time_minutes": 35,
                    "objectives": [
                        "Create VLAN 10 (Engineering) and VLAN 20 (Marketing) on Cisco Catalyst Switches SW1 and SW2.",
                        "Assign FastEthernet access ports to respective VLANs with spanning-tree portfast enabled.",
                        "Configure GigabitEthernet0/1 as an 802.1Q trunk link with native VLAN 99.",
                        "Verify VLAN membership, trunk status, and inter-switch broadcast containment using show commands.",
                    ],
                    "topology_type": "svg",
                    "topology_data": """<svg viewBox="0 0 700 280" xmlns="http://www.w3.org/2000/svg" class="w-full h-auto">
  <defs>
    <linearGradient id="swGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
    <linearGradient id="vlan10Grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#3b82f6"/>
      <stop offset="100%" stop-color="#1d4ed8"/>
    </linearGradient>
    <linearGradient id="vlan20Grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#10b981"/>
      <stop offset="100%" stop-color="#047857"/>
    </linearGradient>
  </defs>
  <!-- Background Grid & Frame -->
  <rect width="700" height="280" rx="12" fill="#090d16" stroke="#1e293b" stroke-width="1.5"/>
  <!-- Switch 1 -->
  <rect x="140" y="80" width="130" height="70" rx="8" fill="url(#swGrad)" stroke="#38bdf8" stroke-width="2"/>
  <text x="205" y="112" fill="#38bdf8" font-size="14" font-weight="bold" font-family="monospace" text-anchor="middle">SW1</text>
  <text x="205" y="132" fill="#94a3b8" font-size="10" font-family="sans-serif" text-anchor="middle">Catalyst 2960</text>
  <!-- Switch 2 -->
  <rect x="430" y="80" width="130" height="70" rx="8" fill="url(#swGrad)" stroke="#38bdf8" stroke-width="2"/>
  <text x="495" y="112" fill="#38bdf8" font-size="14" font-weight="bold" font-family="monospace" text-anchor="middle">SW2</text>
  <text x="495" y="132" fill="#94a3b8" font-size="10" font-family="sans-serif" text-anchor="middle">Catalyst 2960</text>
  <!-- Trunk Link Line -->
  <line x1="270" y1="115" x2="430" y2="115" stroke="#f59e0b" stroke-width="3" stroke-dasharray="6,3"/>
  <text x="350" y="105" fill="#fbbf24" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">802.1Q Trunk (Gi0/1)</text>
  <text x="350" y="135" fill="#fde68a" font-size="10" font-family="sans-serif" text-anchor="middle">Native VLAN 99</text>
  <!-- Host PC1 (VLAN 10) -->
  <circle cx="80" cy="90" r="24" fill="url(#vlan10Grad)" stroke="#60a5fa" stroke-width="1.5"/>
  <text x="80" y="94" fill="#ffffff" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">PC1</text>
  <text x="80" y="130" fill="#93c5fd" font-size="10" font-family="sans-serif" text-anchor="middle">VLAN 10</text>
  <line x1="104" y1="95" x2="140" y2="105" stroke="#60a5fa" stroke-width="2"/>
  <!-- Host PC2 (VLAN 20) -->
  <circle cx="80" cy="190" r="24" fill="url(#vlan20Grad)" stroke="#34d399" stroke-width="1.5"/>
  <text x="80" y="194" fill="#ffffff" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">PC2</text>
  <text x="80" y="230" fill="#6ee7b7" font-size="10" font-family="sans-serif" text-anchor="middle">VLAN 20</text>
  <line x1="104" y1="185" x2="140" y2="125" stroke="#34d399" stroke-width="2"/>
  <!-- Host PC3 (VLAN 10) -->
  <circle cx="620" cy="90" r="24" fill="url(#vlan10Grad)" stroke="#60a5fa" stroke-width="1.5"/>
  <text x="620" y="94" fill="#ffffff" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">PC3</text>
  <text x="620" y="130" fill="#93c5fd" font-size="10" font-family="sans-serif" text-anchor="middle">VLAN 10</text>
  <line x1="560" y1="105" x2="596" y2="95" stroke="#60a5fa" stroke-width="2"/>
  <!-- Host PC4 (VLAN 20) -->
  <circle cx="620" cy="190" r="24" fill="url(#vlan20Grad)" stroke="#34d399" stroke-width="1.5"/>
  <text x="620" y="194" fill="#ffffff" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">PC4</text>
  <text x="620" y="230" fill="#6ee7b7" font-size="10" font-family="sans-serif" text-anchor="middle">VLAN 20</text>
  <line x1="560" y1="125" x2="596" y2="185" stroke="#34d399" stroke-width="2"/>
</svg>""",
                    "addressing_table": [
                        {"device": "PC1", "interface": "NIC", "ip": "192.168.10.11", "subnet": "255.255.255.0", "vlan": "10", "default_gateway": "192.168.10.1"},
                        {"device": "PC2", "interface": "NIC", "ip": "192.168.20.12", "subnet": "255.255.255.0", "vlan": "20", "default_gateway": "192.168.20.1"},
                        {"device": "PC3", "interface": "NIC", "ip": "192.168.10.13", "subnet": "255.255.255.0", "vlan": "10", "default_gateway": "192.168.10.1"},
                        {"device": "PC4", "interface": "NIC", "ip": "192.168.20.14", "subnet": "255.255.255.0", "vlan": "20", "default_gateway": "192.168.20.1"},
                        {"device": "SW1", "interface": "VLAN 99 (SVI)", "ip": "192.168.99.2", "subnet": "255.255.255.0", "vlan": "99", "default_gateway": "N/A"},
                        {"device": "SW2", "interface": "VLAN 99 (SVI)", "ip": "192.168.99.3", "subnet": "255.255.255.0", "vlan": "99", "default_gateway": "N/A"},
                    ],
                    "step_by_step_tasks": [
                        {
                            "step_num": 1,
                            "title": "Create VLANs on SW1 and SW2",
                            "instructions": "Configure VLAN 10 named 'Engineering', VLAN 20 named 'Marketing', and VLAN 99 named 'Management_Native'.",
                            "verify_prompt": "Run 'show vlan brief' to ensure VLANs are present and active."
                        },
                        {
                            "step_num": 2,
                            "title": "Assign Access Ports on SW1",
                            "instructions": "Configure interface Fa0/1 for VLAN 10 (PC1) and Fa0/2 for VLAN 20 (PC2) using 'switchport mode access' and 'switchport access vlan X'. Enable 'spanning-tree portfast'.",
                            "verify_prompt": "Run 'show interfaces status' to verify ports Fa0/1 and Fa0/2 are in VLAN 10 and 20."
                        },
                        {
                            "step_num": 3,
                            "title": "Configure 802.1Q Trunk Link on Gi0/1",
                            "instructions": "Configure interface Gi0/1 on both switches as a trunk using 'switchport mode trunk', set the native VLAN to 99 with 'switchport trunk native vlan 99', and restrict allowed VLANs to 10,20,99.",
                            "verify_prompt": "Run 'show interfaces trunk' to confirm Gi0/1 is trunking with 802.1q and Native VLAN 99."
                        },
                        {
                            "step_num": 4,
                            "title": "Test Connectivity & Isolation",
                            "instructions": "Ping from PC1 to PC3 (same VLAN across trunk, should succeed). Ping from PC1 to PC2 (different VLAN, should fail without Layer 3 routing).",
                            "verify_prompt": "Verify ping results match expected Layer 2 broadcast boundary isolation."
                        }
                    ],
                    "hints": [
                        "Remember to configure 'switchport trunk encapsulation dot1q' if using older multilayer switches before setting mode trunk.",
                        "Always configure the same native VLAN on both sides of a trunk link to avoid CDP native VLAN mismatch errors.",
                        "Enable 'spanning-tree portfast' only on access ports connected to end hosts, never on trunks."
                    ],
                    "solution": """! === SW1 Configuration ===
hostname SW1
!
vlan 10
 name Engineering
vlan 20
 name Marketing
vlan 99
 name Management_Native
!
interface FastEthernet0/1
 description PC1 - Engineering
 switchport mode access
 switchport access vlan 10
 spanning-tree portfast
 no shutdown
!
interface FastEthernet0/2
 description PC2 - Marketing
 switchport mode access
 switchport access vlan 20
 spanning-tree portfast
 no shutdown
!
interface GigabitEthernet0/1
 description Trunk to SW2
 switchport mode trunk
 switchport trunk native vlan 99
 switchport trunk allowed vlan 10,20,99
 no shutdown
!
interface Vlan99
 ip address 192.168.99.2 255.255.255.0
 no shutdown
!
end""",
                    "setup_template_type": "cisco_initial",
                    "setup_template": """hostname Switch
no ip domain-lookup
line con 0
 logging synchronous
 exec-timeout 0 0""",
                    "expected_config_rules": [
                        {"pattern": r"vlan 10", "description": "VLAN 10 created", "section": "vlan", "required": True},
                        {"pattern": r"name Engineering", "description": "VLAN 10 named Engineering", "section": "vlan", "required": True},
                        {"pattern": r"vlan 20", "description": "VLAN 20 created", "section": "vlan", "required": True},
                        {"pattern": r"name Marketing", "description": "VLAN 20 named Marketing", "section": "vlan", "required": True},
                        {"pattern": r"vlan 99", "description": "Native VLAN 99 created", "section": "vlan", "required": True},
                        {"pattern": r"switchport access vlan 10", "description": "Fa0/1 assigned to VLAN 10", "section": "interface FastEthernet0/1", "required": True},
                        {"pattern": r"switchport mode access", "description": "Fa0/1 set to access mode", "section": "interface FastEthernet0/1", "required": True},
                        {"pattern": r"spanning-tree portfast", "description": "PortFast enabled on access ports", "section": "interface FastEthernet0/1", "required": True},
                        {"pattern": r"switchport mode trunk", "description": "Gi0/1 set to trunk mode", "section": "interface GigabitEthernet0/1", "required": True},
                        {"pattern": r"switchport trunk native vlan 99", "description": "Gi0/1 native VLAN set to 99", "section": "interface GigabitEthernet0/1", "required": True},
                        {"pattern": r"switchport trunk allowed vlan (?:.*10.*20.*99|.*10,20,99)", "description": "Allowed VLANs configured on trunk", "section": "interface GigabitEthernet0/1", "required": False},
                    ],
                    "teardown_instructions": "Issue 'write erase' followed by 'delete flash:vlan.dat' and 'reload' to restore switches to factory defaults.",
                    "estimated_cost_usd": 0.00,
                    "free_tier_eligible": True,
                }
            )

        # AWS Lab 1: Multi-AZ VPC with Public & Private Subnets
        vpc_topic = Topic.objects.filter(certification=aws_saa, blueprint_ref="1.2").first()
        if vpc_topic:
            Lab.objects.update_or_create(
                topic=vpc_topic,
                slug="lab-aws-vpc-multi-az-production",
                defaults={
                    "title": "Designing a Production Multi-AZ VPC with Public & Private Subnets",
                    "difficulty": "intermediate",
                    "estimated_time_minutes": 50,
                    "objectives": [
                        "Create a custom VPC (10.0.0.0/16) across 2 Availability Zones (AZ-a and AZ-b).",
                        "Provision 2 Public Subnets (10.0.1.0/24, 10.0.2.0/24) with an Internet Gateway (IGW).",
                        "Provision 2 Private Subnets (10.0.11.0/24, 10.0.12.0/24) for compute and database isolation.",
                        "Deploy a NAT Gateway in Public Subnet A and route private outbound traffic securely.",
                        "Enforce least-privilege security groups and verify outbound internet from private instance without public IP.",
                    ],
                    "topology_type": "svg",
                    "topology_data": """<svg viewBox="0 0 700 300" xmlns="http://www.w3.org/2000/svg" class="w-full h-auto">
  <defs>
    <linearGradient id="vpcGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#020617"/>
    </linearGradient>
  </defs>
  <rect width="700" height="300" rx="12" fill="url(#vpcGrad)" stroke="#334155" stroke-width="1.5"/>
  <!-- VPC Outer Box -->
  <rect x="25" y="25" width="650" height="250" rx="10" fill="none" stroke="#818cf8" stroke-width="2" stroke-dasharray="8,4"/>
  <text x="45" y="48" fill="#a5b4fc" font-size="12" font-weight="bold" font-family="monospace">VPC: 10.0.0.0/16 (Multi-AZ)</text>
  <!-- Internet Gateway -->
  <rect x="300" y="5" width="100" height="36" rx="6" fill="#4338ca" stroke="#818cf8" stroke-width="1.5"/>
  <text x="350" y="28" fill="#ffffff" font-size="11" font-weight="bold" font-family="sans-serif" text-anchor="middle">IGW (Internet)</text>
  <!-- AZ A Box -->
  <rect x="45" y="65" width="295" height="195" rx="8" fill="#1e1b4b" fill-opacity="0.3" stroke="#6366f1" stroke-width="1.2"/>
  <text x="60" y="86" fill="#c7d2fe" font-size="11" font-weight="bold" font-family="monospace">Availability Zone A (us-east-1a)</text>
  <!-- Public Subnet A -->
  <rect x="60" y="98" width="265" height="68" rx="6" fill="#064e3b" fill-opacity="0.4" stroke="#10b981" stroke-width="1.2"/>
  <text x="75" y="118" fill="#6ee7b7" font-size="10" font-weight="bold">Public Subnet A (10.0.1.0/24)</text>
  <rect x="75" y="126" width="110" height="28" rx="4" fill="#059669"/>
  <text x="130" y="144" fill="#ffffff" font-size="10" font-weight="bold" text-anchor="middle">NAT Gateway A</text>
  <!-- Private Subnet A -->
  <rect x="60" y="178" width="265" height="68" rx="6" fill="#1e293b" stroke="#64748b" stroke-width="1.2"/>
  <text x="75" y="198" fill="#cbd5e1" font-size="10" font-weight="bold">Private Subnet A (10.0.11.0/24)</text>
  <text x="75" y="222" fill="#94a3b8" font-size="9">App / DB Instances (No Public IP)</text>
  <!-- AZ B Box -->
  <rect x="360" y="65" width="295" height="195" rx="8" fill="#1e1b4b" fill-opacity="0.3" stroke="#6366f1" stroke-width="1.2"/>
  <text x="375" y="86" fill="#c7d2fe" font-size="11" font-weight="bold" font-family="monospace">Availability Zone B (us-east-1b)</text>
  <!-- Public Subnet B -->
  <rect x="375" y="98" width="265" height="68" rx="6" fill="#064e3b" fill-opacity="0.4" stroke="#10b981" stroke-width="1.2"/>
  <text x="390" y="118" fill="#6ee7b7" font-size="10" font-weight="bold">Public Subnet B (10.0.2.0/24)</text>
  <text x="390" y="142" fill="#a7f3d0" font-size="9">ALB Target Node B</text>
  <!-- Private Subnet B -->
  <rect x="375" y="178" width="265" height="68" rx="6" fill="#1e293b" stroke="#64748b" stroke-width="1.2"/>
  <text x="390" y="198" fill="#cbd5e1" font-size="10" font-weight="bold">Private Subnet B (10.0.12.0/24)</text>
  <text x="390" y="222" fill="#94a3b8" font-size="9">Standby DB Replica / App Node B</text>
</svg>""",
                    "addressing_table": [
                        {"device": "VPC", "interface": "CIDR Block", "ip": "10.0.0.0/16", "subnet": "255.255.0.0", "vlan": "N/A", "default_gateway": "local"},
                        {"device": "Public Subnet A", "interface": "us-east-1a", "ip": "10.0.1.0/24", "subnet": "255.255.255.0", "vlan": "Public", "default_gateway": "IGW"},
                        {"device": "Public Subnet B", "interface": "us-east-1b", "ip": "10.0.2.0/24", "subnet": "255.255.255.0", "vlan": "Public", "default_gateway": "IGW"},
                        {"device": "Private Subnet A", "interface": "us-east-1a", "ip": "10.0.11.0/24", "subnet": "255.255.255.0", "vlan": "Private", "default_gateway": "NAT-GW-A"},
                        {"device": "Private Subnet B", "interface": "us-east-1b", "ip": "10.0.12.0/24", "subnet": "255.255.255.0", "vlan": "Private", "default_gateway": "NAT-GW-A"},
                    ],
                    "step_by_step_tasks": [
                        {
                            "step_num": 1,
                            "title": "Create VPC and Subnets via AWS CLI or Console",
                            "instructions": "Create a VPC with CIDR 10.0.0.0/16 and tag Name='Production-VPC'. Create two public and two private subnets across two AZs.",
                            "verify_prompt": "Run 'aws ec2 describe-subnets --filters Name=vpc-id,Values=<VPC_ID>' to list the 4 subnets."
                        },
                        {
                            "step_num": 2,
                            "title": "Attach Internet Gateway and Configure Public Route Table",
                            "instructions": "Create an Internet Gateway, attach it to your VPC, create a Public Route Table, add default route 0.0.0.0/0 -> IGW, and associate both public subnets.",
                            "verify_prompt": "Verify public subnets have 'enable-map-public-ip-on-launch' enabled."
                        },
                        {
                            "step_num": 3,
                            "title": "Deploy NAT Gateway in Public Subnet A",
                            "instructions": "Allocate an Elastic IP, deploy a NAT Gateway in Public Subnet A. Create a Private Route Table, add default route 0.0.0.0/0 -> NAT Gateway, and associate private subnets.",
                            "verify_prompt": "Verify NAT Gateway status is 'available'."
                        },
                        {
                            "step_num": 4,
                            "title": "Verify Isolation & Egress Connectivity",
                            "instructions": "Deploy a test EC2 instance in Private Subnet A without public IP. Connect via AWS Systems Manager Session Manager (SSM) and curl an external endpoint to verify internet egress.",
                            "verify_prompt": "Confirm curl succeeds while direct inbound SSH from the internet is impossible."
                        }
                    ],
                    "hints": [
                        "Always place the NAT Gateway in a PUBLIC subnet, never in a private subnet!",
                        "Use AWS Systems Manager (SSM) Session Manager instead of an open SSH bastion host for enhanced security.",
                        "Remember that NAT Gateways incur hourly charges (~$0.045/hr) plus data processing fees; always delete the NAT Gateway when finished."
                    ],
                    "solution": """# AWS CLI commands to deploy Multi-AZ VPC:
VPC_ID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=Production-VPC}]' --query 'Vpc.VpcId' --output text)
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames "{\\"Value\\":true}"

# Create Subnets
PUB_SUB_A=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 --availability-zone us-east-1a --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Public-A}]' --query 'Subnet.SubnetId' --output text)
PUB_SUB_B=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.2.0/24 --availability-zone us-east-1b --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Public-B}]' --query 'Subnet.SubnetId' --output text)
PRIV_SUB_A=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.11.0/24 --availability-zone us-east-1a --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Private-A}]' --query 'Subnet.SubnetId' --output text)
PRIV_SUB_B=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.12.0/24 --availability-zone us-east-1b --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Private-B}]' --query 'Subnet.SubnetId' --output text)

# Enable Auto-Assign Public IP on Public Subnets
aws ec2 modify-subnet-attribute --subnet-id $PUB_SUB_A --map-public-ip-on-launch
aws ec2 modify-subnet-attribute --subnet-id $PUB_SUB_B --map-public-ip-on-launch

# Internet Gateway
IGW_ID=$(aws ec2 create-internet-gateway --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=Production-IGW}]' --query 'InternetGateway.InternetGatewayId' --output text)
aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID

# Public Route Table
PUB_RT=$(aws ec2 create-route-table --vpc-id $VPC_ID --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=Public-RT}]' --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-route --route-table-id $PUB_RT --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID
aws ec2 associate-route-table --subnet-id $PUB_SUB_A --route-table-id $PUB_RT
aws ec2 associate-route-table --subnet-id $PUB_SUB_B --route-table-id $PUB_RT

# NAT Gateway
EIP_ALLOC=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)
NAT_GW_ID=$(aws ec2 create-nat-gateway --subnet-id $PUB_SUB_A --allocation-id $EIP_ALLOC --tag-specifications 'ResourceType=natgateway,Tags=[{Key=Name,Value=Production-NAT-A}]' --query 'NatGateway.NatGatewayId' --output text)
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GW_ID

# Private Route Table
PRIV_RT=$(aws ec2 create-route-table --vpc-id $VPC_ID --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=Private-RT}]' --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-route --route-table-id $PRIV_RT --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT_GW_ID
aws ec2 associate-route-table --subnet-id $PRIV_SUB_A --route-table-id $PRIV_RT
aws ec2 associate-route-table --subnet-id $PRIV_SUB_B --route-table-id $PRIV_RT""",
                    "setup_template_type": "terraform",
                    "setup_template": """terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.2"

  name = "production-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b"]
  private_subnets = ["10.0.11.0/24", "10.0.12.0/24"]
  public_subnets  = ["10.0.1.0/24", "10.0.2.0/24"]

  enable_nat_gateway     = true
  single_nat_gateway     = true
  enable_dns_hostnames   = true
  enable_dns_support     = true

  tags = {
    Environment = "production"
    Terraform   = "true"
  }
}""",
                    "aws_verification_checks": [
                        {
                            "service": "ec2",
                            "check_type": "describe_vpcs",
                            "resource_tag": "Production-VPC",
                            "expected": {"cidr": "10.0.0.0/16", "is_default": False}
                        },
                        {
                            "service": "ec2",
                            "check_type": "describe_subnets",
                            "expected_count": 4,
                            "min_azs": 2
                        },
                        {
                            "service": "ec2",
                            "check_type": "describe_nat_gateways",
                            "expected_state": "available"
                        }
                    ],
                    "teardown_instructions": """CRITICAL COST CLEANUP:
1. Delete NAT Gateway immediately after verification:
   aws ec2 delete-nat-gateway --nat-gateway-id <NAT_ID>
2. Wait 2 minutes for NAT GW deletion, then release the Elastic IP:
   aws ec2 release-address --allocation-id <EIP_ALLOC>
3. Terminate any test EC2 instances.
4. Detach and delete Internet Gateway, then delete the VPC.""",
                    "estimated_cost_usd": 0.08,
                    "free_tier_eligible": False,
                }
            )

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded {StudyCertification.objects.count()} certifications and {Topic.objects.count()} topics ({Lab.objects.count()} labs)!"
        ))
