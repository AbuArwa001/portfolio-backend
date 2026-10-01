from django.core.management.base import BaseCommand
from study.models import StudyCertification, Topic, Lab


def make_switch_svg(title: str, subnets: list) -> str:
    """Generates a clean, readable inline SVG network topology diagram."""
    subnet_tags = "".join(
        f'<text x="250" y="{260 + i * 18}" text-anchor="middle" fill="#94a3b8" font-family="monospace" font-size="11">{s}</text>'
        for i, s in enumerate(subnets)
    )
    return f"""<svg viewBox="0 0 500 300" xmlns="http://www.w3.org/2000/svg" class="w-full h-auto">
  <defs>
    <linearGradient id="swGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="4" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>
  <rect width="100%" height="100%" fill="#090d16" rx="12"/>
  <text x="250" y="32" text-anchor="middle" fill="#e2e8f0" font-family="sans-serif" font-size="14" font-weight="bold">{title}</text>
  
  <!-- Links -->
  <line x1="120" y1="120" x2="380" y2="120" stroke="#3b82f6" stroke-width="4" stroke-dasharray="6,4"/>
  <line x1="120" y1="120" x2="120" y2="210" stroke="#64748b" stroke-width="2"/>
  <line x1="380" y1="120" x2="380" y2="210" stroke="#64748b" stroke-width="2"/>

  <!-- Switch 1 -->
  <rect x="70" y="90" width="100" height="60" rx="8" fill="url(#swGrad)" stroke="#3b82f6" stroke-width="2" filter="url(#glow)"/>
  <text x="120" y="120" text-anchor="middle" fill="#60a5fa" font-family="monospace" font-size="13" font-weight="bold">SW-1</text>
  <text x="120" y="138" text-anchor="middle" fill="#94a3b8" font-family="sans-serif" font-size="10">Catalyst 2960</text>
  <text x="180" y="112" fill="#38bdf8" font-family="monospace" font-size="10">Gi0/1</text>

  <!-- Switch 2 -->
  <rect x="330" y="90" width="100" height="60" rx="8" fill="url(#swGrad)" stroke="#3b82f6" stroke-width="2" filter="url(#glow)"/>
  <text x="380" y="120" text-anchor="middle" fill="#60a5fa" font-family="monospace" font-size="13" font-weight="bold">SW-2</text>
  <text x="380" y="138" text-anchor="middle" fill="#94a3b8" font-family="sans-serif" font-size="10">Catalyst 2960</text>
  <text x="310" y="112" fill="#38bdf8" font-family="monospace" font-size="10">Gi0/1</text>

  <!-- Trunk Link Label -->
  <rect x="200" y="106" width="100" height="26" rx="6" fill="#1e1b4b" stroke="#6366f1" stroke-width="1"/>
  <text x="250" y="123" text-anchor="middle" fill="#c7d2fe" font-family="monospace" font-size="10" font-weight="bold">802.1Q TRUNK</text>

  <!-- Endpoints -->
  <rect x="80" y="210" width="80" height="40" rx="6" fill="#1e293b" stroke="#475569" stroke-width="1.5"/>
  <text x="120" y="230" text-anchor="middle" fill="#cbd5e1" font-family="monospace" font-size="11">PC-1 (VLAN 10)</text>
  <text x="120" y="244" text-anchor="middle" fill="#64748b" font-family="monospace" font-size="9">Fa0/1</text>

  <rect x="340" y="210" width="80" height="40" rx="6" fill="#1e293b" stroke="#475569" stroke-width="1.5"/>
  <text x="380" y="230" text-anchor="middle" fill="#cbd5e1" font-family="monospace" font-size="11">PC-2 (VLAN 10)</text>
  <text x="380" y="244" text-anchor="middle" fill="#64748b" font-family="monospace" font-size="9">Fa0/1</text>

  <!-- Subnet Info Footnotes -->
  {subnet_tags}
</svg>"""


def make_router_svg(title: str, subnets: list) -> str:
    """Generates an SVG diagram for Router / Layer 3 routing topologies."""
    subnet_tags = "".join(
        f'<text x="250" y="{260 + i * 18}" text-anchor="middle" fill="#94a3b8" font-family="monospace" font-size="11">{s}</text>'
        for i, s in enumerate(subnets)
    )
    return f"""<svg viewBox="0 0 500 300" xmlns="http://www.w3.org/2000/svg" class="w-full h-auto">
  <defs>
    <linearGradient id="rtrGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e1b4b"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
    <filter id="glowRtr" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="4" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>
  <rect width="100%" height="100%" fill="#090d16" rx="12"/>
  <text x="250" y="32" text-anchor="middle" fill="#e2e8f0" font-family="sans-serif" font-size="14" font-weight="bold">{title}</text>
  
  <!-- WAN Serial/Gig Link -->
  <line x1="130" y1="120" x2="370" y2="120" stroke="#f59e0b" stroke-width="4"/>

  <!-- Router 1 -->
  <circle cx="130" cy="120" r="38" fill="url(#rtrGrad)" stroke="#f59e0b" stroke-width="2.5" filter="url(#glowRtr)"/>
  <text x="130" y="118" text-anchor="middle" fill="#fbbf24" font-family="monospace" font-size="14" font-weight="bold">R1</text>
  <text x="130" y="134" text-anchor="middle" fill="#94a3b8" font-family="sans-serif" font-size="9">ISR 4321</text>
  <text x="180" y="112" fill="#fbbf24" font-family="monospace" font-size="10">Gi0/0/0</text>

  <!-- Router 2 -->
  <circle cx="370" cy="120" r="38" fill="url(#rtrGrad)" stroke="#f59e0b" stroke-width="2.5" filter="url(#glowRtr)"/>
  <text x="370" y="118" text-anchor="middle" fill="#fbbf24" font-family="monospace" font-size="14" font-weight="bold">R2</text>
  <text x="370" y="134" text-anchor="middle" fill="#94a3b8" font-family="sans-serif" font-size="9">ISR 4321</text>
  <text x="310" y="112" fill="#fbbf24" font-family="monospace" font-size="10">Gi0/0/0</text>

  <!-- Link Bandwidth & Network -->
  <rect x="200" y="106" width="100" height="26" rx="6" fill="#292524" stroke="#d97706" stroke-width="1"/>
  <text x="250" y="123" text-anchor="middle" fill="#fed7aa" font-family="monospace" font-size="10" font-weight="bold">10.0.12.0/30</text>

  <!-- LAN R1 -->
  <line x1="130" y1="158" x2="130" y2="210" stroke="#64748b" stroke-width="2"/>
  <rect x="85" y="210" width="90" height="36" rx="6" fill="#1e293b" stroke="#475569" stroke-width="1"/>
  <text x="130" y="228" text-anchor="middle" fill="#cbd5e1" font-family="monospace" font-size="10">LAN 1: 192.168.1.0/24</text>
  <text x="130" y="240" text-anchor="middle" fill="#64748b" font-family="monospace" font-size="9">Gi0/0/1</text>

  <!-- LAN R2 -->
  <line x1="370" y1="158" x2="370" y2="210" stroke="#64748b" stroke-width="2"/>
  <rect x="325" y="210" width="90" height="36" rx="6" fill="#1e293b" stroke="#475569" stroke-width="1"/>
  <text x="370" y="228" text-anchor="middle" fill="#cbd5e1" font-family="monospace" font-size="10">LAN 2: 192.168.2.0/24</text>
  <text x="370" y="240" text-anchor="middle" fill="#64748b" font-family="monospace" font-size="9">Gi0/0/1</text>

  {subnet_tags}
</svg>"""


class Command(BaseCommand):
    help = "Seeds comprehensive production-grade CCNA 200-301 blueprint labs with topology SVGs and config checker rules"

    def handle(self, *args, **options):
        ccna = StudyCertification.objects.filter(code="CCNA-200-301").first()
        if not ccna:
            self.stdout.write(self.style.ERROR("CCNA certification record not found. Run seed_study_topics first."))
            return

        labs_data = [
            # 1. Topic 2.1: VLANs & Segmentation
            {
                "topic_ref": "2.1",
                "title": "Configuring VLANs, Access Ports, and 802.1Q Trunking",
                "slug": "configuring-vlans-trunks",
                "difficulty": "beginner",
                "estimated_time_minutes": 35,
                "topology_type": "svg",
                "topology_data": make_switch_svg("VLANs, Access Ports & 802.1Q Trunking Topology", ["Trunk: GigabitEthernet0/1", "VLAN 10: Sales (192.168.10.0/24)", "VLAN 20: Engineering (192.168.20.0/24)", "VLAN 99: Native VLAN"]),
                "prerequisites": "Basic understanding of switchports, broadcast domains, and 802.1Q frame tagging.",
                "objectives": [
                    "Create VLAN 10 (Sales) and VLAN 20 (Engineering) on both switches",
                    "Assign FastEthernet0/1 to VLAN 10 and FastEthernet0/2 to VLAN 20 as access ports",
                    "Configure GigabitEthernet0/1 as an 802.1Q trunk port with native VLAN 99",
                    "Verify trunk status and VLAN port assignments using show interfaces trunk and show vlan brief"
                ],
                "addressing_table": [
                    {"device": "SW-1", "interface": "VLAN 10", "ip": "192.168.10.2", "subnet": "255.255.255.0", "default_gateway": "N/A"},
                    {"device": "SW-1", "interface": "VLAN 99", "ip": "192.168.99.2", "subnet": "255.255.255.0", "default_gateway": "N/A"},
                    {"device": "SW-2", "interface": "VLAN 99", "ip": "192.168.99.3", "subnet": "255.255.255.0", "default_gateway": "N/A"},
                    {"device": "PC-1", "interface": "NIC", "ip": "192.168.10.10", "subnet": "255.255.255.0", "default_gateway": "192.168.10.1"},
                    {"device": "PC-2", "interface": "NIC", "ip": "192.168.10.11", "subnet": "255.255.255.0", "default_gateway": "192.168.10.1"},
                ],
                "step_by_step_tasks": [
                    {
                        "step_num": 1,
                        "title": "Create and Name VLANs",
                        "instructions": "Enter global configuration mode. Create VLAN 10 named 'Sales' and VLAN 20 named 'Engineering'. Repeat on SW-2.",
                        "verify_prompt": "Run 'show vlan brief' to ensure VLANs are active."
                    },
                    {
                        "step_num": 2,
                        "title": "Assign Access Switchports",
                        "instructions": "Configure interface FastEthernet0/1 with 'switchport mode access' and 'switchport access vlan 10'.",
                        "verify_prompt": "Confirm FastEthernet0/1 appears under VLAN 10 in 'show vlan brief'."
                    },
                    {
                        "step_num": 3,
                        "title": "Establish 802.1Q Trunk Link",
                        "instructions": "Under interface GigabitEthernet0/1, set 'switchport mode trunk' and change the native VLAN to 99 using 'switchport trunk native vlan 99'.",
                        "verify_prompt": "Execute 'show interfaces trunk' and verify Gi0/1 shows Status 'trunking' and Native vlan '99'."
                    }
                ],
                "hints": [
                    "Remember that Cisco switches default to Native VLAN 1. Both ends must match to avoid CDP mismatch syslog warnings.",
                    "If your switch requires encapsulation specification before trunking, issue 'switchport trunk encapsulation dot1q' first."
                ],
                "setup_template": """hostname SW-1
!
interface GigabitEthernet0/1
 shutdown
!
interface FastEthernet0/1
 shutdown
!
end""",
                "setup_template_type": "cisco_initial",
                "solution": """SW-1# configure terminal
vlan 10
 name Sales
vlan 20
 name Engineering
vlan 99
 name Management_Native
!
interface FastEthernet0/1
 switchport mode access
 switchport access vlan 10
 no shutdown
!
interface GigabitEthernet0/1
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 99
 switchport trunk allowed vlan 10,20,99
 no shutdown
end""",
                "expected_config_rules": [
                    {"pattern": r"vlan\s+10\b", "description": "VLAN 10 created", "weight": 2, "help_tip": "Add 'vlan 10' under global configuration."},
                    {"pattern": r"vlan\s+20\b", "description": "VLAN 20 created", "weight": 2, "help_tip": "Add 'vlan 20' under global configuration."},
                    {"section": "interface fastethernet0/1", "pattern": r"switchport\s+access\s+vlan\s+10\b", "description": "FastEthernet0/1 assigned to VLAN 10", "weight": 2, "help_tip": "Issue 'switchport access vlan 10' under FastEthernet0/1."},
                    {"section": "interface gigabitethernet0/1", "pattern": r"switchport\s+mode\s+trunk\b", "description": "GigabitEthernet0/1 set to trunk mode", "weight": 2, "help_tip": "Issue 'switchport mode trunk' on Gi0/1."},
                    {"section": "interface gigabitethernet0/1", "pattern": r"switchport\s+trunk\s+native\s+vlan\s+99\b", "description": "Native VLAN 99 configured on trunk Gi0/1", "weight": 2, "help_tip": "Issue 'switchport trunk native vlan 99' on Gi0/1."},
                ]
            },

            # 2. Topic 2.4: EtherChannel (LACP & PAgP)
            {
                "topic_ref": "2.4",
                "title": "LACP EtherChannel (802.3ad) Multi-Link Aggregation",
                "slug": "lacp-etherchannel-aggregation",
                "difficulty": "intermediate",
                "estimated_time_minutes": 40,
                "topology_type": "svg",
                "topology_data": make_switch_svg("LACP EtherChannel Port-Channel 1 Topology", ["Bundle: Gi0/1 + Gi0/2 into Port-Channel 1", "Protocol: 802.3ad LACP (active / passive)", "Trunking: 802.1Q across Port-Channel 1"]),
                "prerequisites": "Understanding of Spanning Tree Protocol blocking redundant links without aggregation.",
                "objectives": [
                    "Bundle physical interfaces GigabitEthernet0/1 and GigabitEthernet0/2 into Port-channel 1",
                    "Configure open standard LACP using 'channel-group 1 mode active'",
                    "Configure Port-channel 1 as an 802.1Q trunk",
                    "Verify EtherChannel status using 'show etherchannel summary'"
                ],
                "addressing_table": [
                    {"device": "SW-1", "interface": "Port-channel 1", "ip": "Unnumbered (Layer 2 Trunk)", "subnet": "N/A", "default_gateway": "N/A"},
                    {"device": "SW-2", "interface": "Port-channel 1", "ip": "Unnumbered (Layer 2 Trunk)", "subnet": "N/A", "default_gateway": "N/A"},
                ],
                "step_by_step_tasks": [
                    {
                        "step_num": 1,
                        "title": "Bundle Physical Interfaces",
                        "instructions": "Select interface range Gi0/1 - 2. Issue 'channel-group 1 mode active' to initiate LACP.",
                        "verify_prompt": "Run 'show etherchannel summary' and confirm Port-channel 1 appears."
                    },
                    {
                        "step_num": 2,
                        "title": "Configure Port-Channel Logical Interface",
                        "instructions": "Enter 'interface port-channel 1' and configure 'switchport mode trunk'.",
                        "verify_prompt": "Inspect 'show interfaces trunk' to verify Po1 is forwarding."
                    }
                ],
                "hints": [
                    "Ensure speed and duplex match exactly on both physical interfaces before bundling.",
                    "Always apply trunk and VLAN configs to the logical 'interface Port-channel 1', not the member ports directly."
                ],
                "setup_template": """hostname SW-1
!
interface GigabitEthernet0/1
 shutdown
!
interface GigabitEthernet0/2
 shutdown
!
end""",
                "setup_template_type": "cisco_initial",
                "solution": """SW-1# configure terminal
interface range GigabitEthernet0/1 - 2
 channel-group 1 mode active
 no shutdown
!
interface Port-channel 1
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 99
 no shutdown
end""",
                "expected_config_rules": [
                    {"pattern": r"channel-group\s+1\s+mode\s+active\b", "description": "LACP channel-group 1 mode active on member ports", "weight": 3, "help_tip": "Use 'channel-group 1 mode active' under interface range Gi0/1 - 2."},
                    {"pattern": r"interface\s+port-channel\s+1\b", "description": "Logical Port-channel 1 created", "weight": 2, "help_tip": "Enter 'interface Port-channel 1' to configure the bundle."},
                    {"section": "interface port-channel 1", "pattern": r"switchport\s+mode\s+trunk\b", "description": "Port-channel 1 configured as trunk", "weight": 3, "help_tip": "Add 'switchport mode trunk' under interface Port-channel 1."},
                    {"pattern": r"no\s+shutdown\b", "description": "Interfaces enabled with no shutdown", "weight": 2, "help_tip": "Ensure ports are un-shutdown."},
                ]
            },

            # 3. Topic 2.5: Rapid Spanning Tree Protocol (RSTP 802.1w)
            {
                "topic_ref": "2.5",
                "title": "Rapid Spanning Tree (RSTP 802.1w) & Root Bridge Tuning",
                "slug": "rstp-root-bridge-tuning",
                "difficulty": "intermediate",
                "estimated_time_minutes": 35,
                "topology_type": "svg",
                "topology_data": make_switch_svg("Rapid PVST+ & Root Bridge Priority Topology", ["Spanning-tree mode: rapid-pvst", "SW-1 Primary Root: Priority 4096 (VLAN 10,20)", "SW-2 Secondary Root: Priority 8192"]),
                "prerequisites": "Understanding of Bridge Protocol Data Units (BPDUs), bridge priority, and root election.",
                "objectives": [
                    "Change spanning tree mode to Rapid PVST+ on all switches",
                    "Configure SW-1 as the primary root bridge for VLAN 10 and VLAN 20 (priority 4096)",
                    "Configure SW-2 as the secondary root bridge for VLAN 10 and VLAN 20 (priority 8192)",
                    "Verify root bridge role and port roles using 'show spanning-tree vlan 10'"
                ],
                "addressing_table": [],
                "step_by_step_tasks": [
                    {
                        "step_num": 1,
                        "title": "Enable Rapid PVST+",
                        "instructions": "Execute 'spanning-tree mode rapid-pvst' in global configuration mode.",
                        "verify_prompt": "Run 'show spanning-tree summary' and check mode."
                    },
                    {
                        "step_num": 2,
                        "title": "Set Bridge Priority",
                        "instructions": "Configure 'spanning-tree vlan 10,20 priority 4096' on SW-1. On SW-2 configure priority 8192.",
                        "verify_prompt": "Run 'show spanning-tree vlan 10' and confirm 'This bridge is the root'."
                    }
                ],
                "hints": [
                    "Remember bridge priority must be configured in increments of 4096 due to the 12-bit system ID extension (VLAN ID).",
                    "Alternatively, you can use the macro 'spanning-tree vlan 10 root primary'."
                ],
                "setup_template": """hostname SW-1
!
vlan 10
vlan 20
end""",
                "setup_template_type": "cisco_initial",
                "solution": """SW-1# configure terminal
spanning-tree mode rapid-pvst
spanning-tree vlan 10,20 priority 4096
end""",
                "expected_config_rules": [
                    {"pattern": r"spanning-tree\s+mode\s+rapid-pvst\b", "description": "Rapid PVST+ spanning tree mode active", "weight": 5, "help_tip": "Configure 'spanning-tree mode rapid-pvst'."},
                    {"pattern": r"spanning-tree\s+vlan\s+(10,20|10\s+root\s+primary|10,20\s+priority\s+4096)", "description": "Primary root bridge priority set for VLAN 10 & 20", "weight": 5, "help_tip": "Use 'spanning-tree vlan 10,20 priority 4096'."},
                ]
            },

            # 4. Topic 3.3: IPv4 & IPv6 Static Routing
            {
                "topic_ref": "3.3",
                "title": "IPv4 & IPv6 Static Routing with Floating Backup Route",
                "slug": "static-routing-floating-backup",
                "difficulty": "intermediate",
                "estimated_time_minutes": 35,
                "topology_type": "svg",
                "topology_data": make_router_svg("IPv4 & IPv6 Static & Floating Backup Routes", ["Primary WAN: 10.0.12.0/30 (Gi0/0/0)", "Backup WAN: 10.0.21.0/30 via AD 10", "Default Route: 0.0.0.0/0 & ::/0"]),
                "prerequisites": "Administrative distance concept (Static = 1, Floating Static > 1).",
                "objectives": [
                    "Configure primary static default route 0.0.0.0 0.0.0.0 via 10.0.12.2",
                    "Configure floating backup static route 0.0.0.0 0.0.0.0 via 10.0.21.2 with Administrative Distance 10",
                    "Configure IPv6 default route ::/0 via 2001:db8:12::2",
                    "Verify routing table using 'show ip route' and 'show ipv6 route'"
                ],
                "addressing_table": [
                    {"device": "R1", "interface": "GigabitEthernet0/0/0 (Primary)", "ip": "10.0.12.1", "subnet": "255.255.255.252", "default_gateway": "N/A"},
                    {"device": "R1", "interface": "GigabitEthernet0/0/1 (Backup)", "ip": "10.0.21.1", "subnet": "255.255.255.252", "default_gateway": "N/A"},
                    {"device": "R2", "interface": "GigabitEthernet0/0/0", "ip": "10.0.12.2", "subnet": "255.255.255.252", "default_gateway": "N/A"},
                ],
                "step_by_step_tasks": [
                    {
                        "step_num": 1,
                        "title": "Configure IPv4 Primary Static Route",
                        "instructions": "Add standard default route 'ip route 0.0.0.0 0.0.0.0 10.0.12.2'.",
                        "verify_prompt": "Run 'show ip route' and check for 'S* 0.0.0.0/0'."
                    },
                    {
                        "step_num": 2,
                        "title": "Configure Floating Backup Route",
                        "instructions": "Add backup route 'ip route 0.0.0.0 0.0.0.0 10.0.21.2 10'.",
                        "verify_prompt": "Verify backup route only shows up when primary link is down."
                    },
                    {
                        "step_num": 3,
                        "title": "Configure IPv6 Unicast Routing & Default Route",
                        "instructions": "Enable 'ipv6 unicast-routing' and configure 'ipv6 route ::/0 2001:db8:12::2'.",
                        "verify_prompt": "Run 'show ipv6 route' and inspect S ::/0."
                    }
                ],
                "hints": [
                    "Remember to enable 'ipv6 unicast-routing' globally before configuring IPv6 routing.",
                    "A floating static route must have an AD higher than the primary route (default static AD is 1)."
                ],
                "setup_template": """hostname R1
!
interface GigabitEthernet0/0/0
 ip address 10.0.12.1 255.255.255.252
 ipv6 address 2001:db8:12::1/64
 no shutdown
!
end""",
                "setup_template_type": "cisco_initial",
                "solution": """R1# configure terminal
ipv6 unicast-routing
!
ip route 0.0.0.0 0.0.0.0 10.0.12.2
ip route 0.0.0.0 0.0.0.0 10.0.21.2 10
!
ipv6 route ::/0 2001:db8:12::2
end""",
                "expected_config_rules": [
                    {"pattern": r"ipv6\s+unicast-routing\b", "description": "IPv6 routing enabled globally", "weight": 2, "help_tip": "Enable with 'ipv6 unicast-routing'."},
                    {"pattern": r"ip\s+route\s+0\.0\.0\.0\s+0\.0\.0\.0\s+10\.0\.12\.2\b", "description": "Primary IPv4 default route configured via 10.0.12.2", "weight": 3, "help_tip": "Add 'ip route 0.0.0.0 0.0.0.0 10.0.12.2'."},
                    {"pattern": r"ip\s+route\s+0\.0\.0\.0\s+0\.0\.0\.0\s+10\.0\.21\.2\s+10\b", "description": "Floating backup route with AD 10 configured", "weight": 3, "help_tip": "Add 'ip route 0.0.0.0 0.0.0.0 10.0.21.2 10'."},
                    {"pattern": r"ipv6\s+route\s+::/0\s+2001:db8:12::2\b", "description": "IPv6 default route configured", "weight": 2, "help_tip": "Add 'ipv6 route ::/0 2001:db8:12::2'."},
                ]
            },

            # 5. Topic 3.4: Single-Area OSPFv2
            {
                "topic_ref": "3.4",
                "title": "Single-Area OSPFv2 Point-to-Point Configuration",
                "slug": "single-area-ospfv2-configuration",
                "difficulty": "intermediate",
                "estimated_time_minutes": 40,
                "topology_type": "svg",
                "topology_data": make_router_svg("Single-Area OSPFv2 Backbone (Area 0) Topology", ["R1 Router-ID: 1.1.1.1", "R2 Router-ID: 2.2.2.2", "Area 0: 10.0.12.0/30", "LAN 1: 192.168.1.0/24 (Passive)"]),
                "prerequisites": "Knowledge of OSPF neighbor states, router-ids, wildcard masks, and passive-interfaces.",
                "objectives": [
                    "Enable OSPF process 1 and assign manual Router-ID 1.1.1.1",
                    "Advertise the WAN link (10.0.12.0/30) into OSPF Area 0 using wildcard mask 0.0.0.3",
                    "Advertise LAN 1 (192.168.1.0/24) into Area 0",
                    "Set LAN interface GigabitEthernet0/0/1 as passive-interface",
                    "Verify OSPF adjacency using 'show ip ospf neighbor' and 'show ip route ospf'"
                ],
                "addressing_table": [
                    {"device": "R1", "interface": "Gi0/0/0 (WAN)", "ip": "10.0.12.1", "subnet": "255.255.255.252", "default_gateway": "N/A"},
                    {"device": "R1", "interface": "Gi0/0/1 (LAN)", "ip": "192.168.1.1", "subnet": "255.255.255.0", "default_gateway": "N/A"},
                    {"device": "R2", "interface": "Gi0/0/0 (WAN)", "ip": "10.0.12.2", "subnet": "255.255.255.252", "default_gateway": "N/A"},
                ],
                "step_by_step_tasks": [
                    {
                        "step_num": 1,
                        "title": "Configure OSPF Process & Router ID",
                        "instructions": "Enter 'router ospf 1' and configure 'router-id 1.1.1.1'.",
                        "verify_prompt": "Run 'show ip ospf' and verify Router ID."
                    },
                    {
                        "step_num": 2,
                        "title": "Advertise Networks with Wildcard Masks",
                        "instructions": "Use 'network 10.0.12.0 0.0.0.3 area 0' and 'network 192.168.1.0 0.0.0.255 area 0'.",
                        "verify_prompt": "Check 'show ip protocols' for routing networks."
                    },
                    {
                        "step_num": 3,
                        "title": "Prevent OSPF Hellos on User LAN",
                        "instructions": "Under 'router ospf 1', add 'passive-interface GigabitEthernet0/0/1'.",
                        "verify_prompt": "Confirm Gi0/0/1 is listed under Passive Interfaces in 'show ip protocols'."
                    }
                ],
                "hints": [
                    "Remember that wildcard mask is calculated as (255.255.255.255 - Subnet Mask). For /30, 255.255.255.255 - 255.255.255.252 = 0.0.0.3.",
                    "Passive interfaces stop sending Hello packets but continue advertising the connected network prefix."
                ],
                "setup_template": """hostname R1
!
interface GigabitEthernet0/0/0
 ip address 10.0.12.1 255.255.255.252
 no shutdown
!
interface GigabitEthernet0/0/1
 ip address 192.168.1.1 255.255.255.0
 no shutdown
!
end""",
                "setup_template_type": "cisco_initial",
                "solution": """R1# configure terminal
router ospf 1
 router-id 1.1.1.1
 network 10.0.12.0 0.0.0.3 area 0
 network 192.168.1.0 0.0.0.255 area 0
 passive-interface GigabitEthernet0/0/1
end""",
                "expected_config_rules": [
                    {"pattern": r"router\s+ospf\s+1\b", "description": "OSPF process 1 initiated", "weight": 2, "help_tip": "Start with 'router ospf 1'."},
                    {"pattern": r"router-id\s+1\.1\.1\.1\b", "description": "Manual Router-ID 1.1.1.1 configured", "weight": 2, "help_tip": "Configure 'router-id 1.1.1.1' inside OSPF."},
                    {"pattern": r"network\s+10\.0\.12\.0\s+0\.0\.0\.3\s+area\s+0\b", "description": "WAN link advertised into Area 0 with 0.0.0.3 wildcard", "weight": 3, "help_tip": "Use 'network 10.0.12.0 0.0.0.3 area 0'."},
                    {"pattern": r"network\s+192\.168\.1\.0\s+0\.0\.0\.255\s+area\s+0\b", "description": "LAN 1 advertised into Area 0", "weight": 2, "help_tip": "Use 'network 192.168.1.0 0.0.0.255 area 0'."},
                    {"pattern": r"passive-interface\s+(gigabitethernet0/0/1|gi0/0/1)\b", "description": "LAN interface set as passive-interface", "weight": 2, "help_tip": "Add 'passive-interface GigabitEthernet0/0/1'."},
                ]
            },

            # 6. Topic 4.1: NAT & PAT
            {
                "topic_ref": "4.1",
                "title": "Inside Source Port Address Translation (NAT Overload / PAT)",
                "slug": "nat-overload-pat-configuration",
                "difficulty": "intermediate",
                "estimated_time_minutes": 35,
                "topology_type": "svg",
                "topology_data": make_router_svg("Inside Source NAT Overload (PAT) Topology", ["Inside Network: 192.168.1.0/24 (Gi0/0/1)", "Outside Public Interface: Gi0/0/0 (203.0.113.1)", "ACL 1: Permit Inside LAN"]),
                "prerequisites": "Understanding of private IPv4 address spaces and public Internet translation.",
                "objectives": [
                    "Designate inside and outside NAT interfaces",
                    "Create standard ACL 1 to permit inside subnet 192.168.1.0/24",
                    "Configure PAT overload translation to outside interface GigabitEthernet0/0/0",
                    "Verify active translations using 'show ip nat translations'"
                ],
                "addressing_table": [
                    {"device": "R1", "interface": "GigabitEthernet0/0/0 (Outside)", "ip": "203.0.113.1", "subnet": "255.255.255.248", "default_gateway": "203.0.113.2"},
                    {"device": "R1", "interface": "GigabitEthernet0/0/1 (Inside)", "ip": "192.168.1.1", "subnet": "255.255.255.0", "default_gateway": "N/A"},
                ],
                "step_by_step_tasks": [
                    {
                        "step_num": 1,
                        "title": "Define NAT Roles on Interfaces",
                        "instructions": "Enter Gi0/0/1 and apply 'ip nat inside'. Enter Gi0/0/0 and apply 'ip nat outside'.",
                        "verify_prompt": "Run 'show ip nat statistics' to confirm roles."
                    },
                    {
                        "step_num": 2,
                        "title": "Create Access Control List",
                        "instructions": "Configure 'access-list 1 permit 192.168.1.0 0.0.0.255'.",
                        "verify_prompt": "Inspect 'show access-lists'."
                    },
                    {
                        "step_num": 3,
                        "title": "Enable PAT Overload",
                        "instructions": "Execute 'ip nat inside source list 1 interface GigabitEthernet0/0/0 overload'.",
                        "verify_prompt": "Ping from LAN to external address and verify entries in 'show ip nat translations'."
                    }
                ],
                "hints": [
                    "Do NOT forget the 'overload' keyword at the end of the NAT statement to enable Port Address Translation.",
                    "Verify the default route exists towards the outside ISP."
                ],
                "setup_template": """hostname R1
!
interface GigabitEthernet0/0/0
 ip address 203.0.113.1 255.255.255.248
 no shutdown
!
interface GigabitEthernet0/0/1
 ip address 192.168.1.1 255.255.255.0
 no shutdown
!
end""",
                "setup_template_type": "cisco_initial",
                "solution": """R1# configure terminal
interface GigabitEthernet0/0/1
 ip nat inside
!
interface GigabitEthernet0/0/0
 ip nat outside
!
access-list 1 permit 192.168.1.0 0.0.0.255
!
ip nat inside source list 1 interface GigabitEthernet0/0/0 overload
end""",
                "expected_config_rules": [
                    {"section": "interface gigabitethernet0/0/1", "pattern": r"ip\s+nat\s+inside\b", "description": "GigabitEthernet0/0/1 designated as ip nat inside", "weight": 2.5, "help_tip": "Apply 'ip nat inside' under Gi0/0/1."},
                    {"section": "interface gigabitethernet0/0/0", "pattern": r"ip\s+nat\s+outside\b", "description": "GigabitEthernet0/0/0 designated as ip nat outside", "weight": 2.5, "help_tip": "Apply 'ip nat outside' under Gi0/0/0."},
                    {"pattern": r"access-list\s+1\s+permit\s+192\.168\.1\.0\s+0\.0\.0\.255\b", "description": "ACL 1 permits 192.168.1.0/24", "weight": 2.5, "help_tip": "Add 'access-list 1 permit 192.168.1.0 0.0.0.255'."},
                    {"pattern": r"ip\s+nat\s+inside\s+source\s+list\s+1\s+interface\s+(gigabitethernet0/0/0|gi0/0/0)\s+overload\b", "description": "PAT overload command configured on Gi0/0/0", "weight": 2.5, "help_tip": "Add 'ip nat inside source list 1 interface Gi0/0/0 overload'."},
                ]
            },

            # 7. Topic 5.4: Extended IPv4 ACLs
            {
                "topic_ref": "5.4",
                "title": "Extended IPv4 Access Control Lists (Port & State Filtering)",
                "slug": "extended-ipv4-acl-filtering",
                "difficulty": "intermediate",
                "estimated_time_minutes": 35,
                "topology_type": "svg",
                "topology_data": make_router_svg("Extended IPv4 ACL Security Hardening", ["ACL: FILTER_INBOUND on Gi0/0/1", "Rule 1: Permit HTTP/HTTPS to Web Server", "Rule 2: Deny Telnet (port 23)", "Rule 3: Permit established TCP"]),
                "prerequisites": "Layer 4 port numbers (HTTP 80, HTTPS 443, Telnet 23, SSH 22).",
                "objectives": [
                    "Create named extended ACL 'FILTER_INBOUND'",
                    "Permit web traffic (TCP 80, 443) from any source to Web Server (192.168.1.10)",
                    "Explicitly deny Telnet (TCP 23) from any source to internal network with log option",
                    "Permit established TCP connections returning from external requests",
                    "Apply ACL inbound on interface GigabitEthernet0/0/1"
                ],
                "addressing_table": [
                    {"device": "R1", "interface": "Gi0/0/1", "ip": "192.168.1.1", "subnet": "255.255.255.0", "default_gateway": "N/A"},
                    {"device": "Web Server", "interface": "NIC", "ip": "192.168.1.10", "subnet": "255.255.255.0", "default_gateway": "192.168.1.1"},
                ],
                "step_by_step_tasks": [
                    {
                        "step_num": 1,
                        "title": "Create Named Extended ACL",
                        "instructions": "Enter 'ip access-list extended FILTER_INBOUND'.",
                        "verify_prompt": "Confirm CLI moves to (config-ext-nacl)# prompt."
                    },
                    {
                        "step_num": 2,
                        "title": "Add Port-Specific Rules",
                        "instructions": "Permit TCP port 80/443 to host 192.168.1.10. Deny TCP port 23 any any.",
                        "verify_prompt": "Run 'show access-lists FILTER_INBOUND'."
                    },
                    {
                        "step_num": 3,
                        "title": "Apply ACL to Interface",
                        "instructions": "Under interface GigabitEthernet0/0/1, apply 'ip access-group FILTER_INBOUND in'.",
                        "verify_prompt": "Run 'show ip interface GigabitEthernet0/0/1' and check Inbound access list."
                    }
                ],
                "hints": [
                    "Remember extended ACLs should be placed as close to the traffic source as possible to save network bandwidth.",
                    "Always remember the implicit deny at the end of every Cisco ACL."
                ],
                "setup_template": """hostname R1
!
interface GigabitEthernet0/0/1
 ip address 192.168.1.1 255.255.255.0
 no shutdown
!
end""",
                "setup_template_type": "cisco_initial",
                "solution": """R1# configure terminal
ip access-list extended FILTER_INBOUND
 permit tcp any host 192.168.1.10 eq 80
 permit tcp any host 192.168.1.10 eq 443
 deny tcp any any eq 23 log
 permit tcp any any established
 permit icmp any any echo-reply
!
interface GigabitEthernet0/0/1
 ip access-group FILTER_INBOUND in
end""",
                "expected_config_rules": [
                    {"pattern": r"ip\s+access-list\s+extended\s+FILTER_INBOUND\b", "description": "Named extended ACL FILTER_INBOUND created", "weight": 2.5, "help_tip": "Create with 'ip access-list extended FILTER_INBOUND'."},
                    {"pattern": r"permit\s+tcp\s+any\s+host\s+192\.168\.1\.10\s+eq\s+(80|www)\b", "description": "Permit HTTP traffic to Web Server", "weight": 2.5, "help_tip": "Add 'permit tcp any host 192.168.1.10 eq 80'."},
                    {"pattern": r"deny\s+tcp\s+any\s+any\s+eq\s+(23|telnet)\b", "description": "Explicit deny of insecure Telnet traffic", "weight": 2.5, "help_tip": "Add 'deny tcp any any eq 23'."},
                    {"section": "interface gigabitethernet0/0/1", "pattern": r"ip\s+access-group\s+FILTER_INBOUND\s+in\b", "description": "ACL applied inbound on Gi0/0/1", "weight": 2.5, "help_tip": "Apply with 'ip access-group FILTER_INBOUND in' under Gi0/0/1."},
                ]
            },

            # 8. Topic 5.5: Switchport Port Security
            {
                "topic_ref": "5.5",
                "title": "Switchport Port Security (Sticky MAC & Violation Modes)",
                "slug": "switchport-port-security-hardening",
                "difficulty": "intermediate",
                "estimated_time_minutes": 30,
                "topology_type": "svg",
                "topology_data": make_switch_svg("Switchport Port Security Hardening Topology", ["Interface: FastEthernet0/1 to User PC", "Max MACs: 2", "Sticky Learning Active", "Violation Mode: Restrict"]),
                "prerequisites": "Understanding Layer 2 MAC flooding attacks and CAM table starvation.",
                "objectives": [
                    "Enable port security on access port FastEthernet0/1",
                    "Configure maximum allowed MAC addresses to 2",
                    "Enable dynamic sticky MAC address learning",
                    "Set the security violation mode to 'restrict'",
                    "Verify port security status using 'show port-security interface FastEthernet0/1'"
                ],
                "addressing_table": [],
                "step_by_step_tasks": [
                    {
                        "step_num": 1,
                        "title": "Enable Port Security",
                        "instructions": "Enter interface FastEthernet0/1. Set 'switchport mode access' then 'switchport port-security'.",
                        "verify_prompt": "Run 'show port-security interface Fa0/1' and check 'Port Security: Enabled'."
                    },
                    {
                        "step_num": 2,
                        "title": "Set Limits and Violation Mode",
                        "instructions": "Issue 'switchport port-security maximum 2' and 'switchport port-security violation restrict'.",
                        "verify_prompt": "Check violation mode displays 'Restrict'."
                    },
                    {
                        "step_num": 3,
                        "title": "Enable Sticky MAC Learning",
                        "instructions": "Issue 'switchport port-security mac-address sticky'.",
                        "verify_prompt": "Inspect running-config to see sticky MAC automatically appended."
                    }
                ],
                "hints": [
                    "You cannot enable port security on a dynamic port; you must explicitly set 'switchport mode access' first.",
                    "Violation mode 'restrict' increments the security counter and sends SNMP traps without disabling the entire port."
                ],
                "setup_template": """hostname SW-1
!
interface FastEthernet0/1
 switchport mode access
 shutdown
!
end""",
                "setup_template_type": "cisco_initial",
                "solution": """SW-1# configure terminal
interface FastEthernet0/1
 switchport mode access
 switchport port-security
 switchport port-security maximum 2
 switchport port-security violation restrict
 switchport port-security mac-address sticky
 no shutdown
end""",
                "expected_config_rules": [
                    {"section": "interface fastethernet0/1", "pattern": r"switchport\s+port-security\b", "description": "Port security enabled on Fa0/1", "weight": 2.5, "help_tip": "Issue 'switchport port-security' under Fa0/1."},
                    {"section": "interface fastethernet0/1", "pattern": r"switchport\s+port-security\s+maximum\s+2\b", "description": "Maximum MAC addresses set to 2", "weight": 2.5, "help_tip": "Add 'switchport port-security maximum 2'."},
                    {"section": "interface fastethernet0/1", "pattern": r"switchport\s+port-security\s+violation\s+restrict\b", "description": "Violation mode set to restrict", "weight": 2.5, "help_tip": "Add 'switchport port-security violation restrict'."},
                    {"section": "interface fastethernet0/1", "pattern": r"switchport\s+port-security\s+mac-address\s+sticky\b", "description": "Sticky MAC learning enabled", "weight": 2.5, "help_tip": "Add 'switchport port-security mac-address sticky'."},
                ]
            }
        ]

        created_count = 0
        for l_data in labs_data:
            topic = Topic.objects.filter(certification=ccna, blueprint_ref=l_data["topic_ref"]).first()
            if not topic:
                self.stdout.write(self.style.WARNING(f"Topic {l_data['topic_ref']} not found in DB. Skipping lab."))
                continue

            lab, created = Lab.objects.update_or_create(
                topic=topic,
                slug=l_data["slug"],
                defaults={
                    "title": l_data["title"],
                    "difficulty": l_data["difficulty"],
                    "estimated_time_minutes": l_data["estimated_time_minutes"],
                    "topology_type": l_data["topology_type"],
                    "topology_data": l_data["topology_data"],
                    "prerequisites": l_data["prerequisites"],
                    "objectives": l_data["objectives"],
                    "addressing_table": l_data["addressing_table"],
                    "step_by_step_tasks": l_data["step_by_step_tasks"],
                    "hints": l_data["hints"],
                    "setup_template": l_data["setup_template"],
                    "setup_template_type": l_data["setup_template_type"],
                    "solution": l_data["solution"],
                    "expected_config_rules": l_data["expected_config_rules"],
                    "order": 1,
                }
            )
            created_count += 1
            self.stdout.write(f"  + Seeded Lab: {lab.title} (Topic {topic.blueprint_ref})")

        self.stdout.write(self.style.SUCCESS(f"Successfully configured {created_count} authentic CCNA production labs!"))
