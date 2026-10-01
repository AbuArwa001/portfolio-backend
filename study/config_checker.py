import re
from typing import List, Dict, Any, Tuple


# Common Cisco IOS command normalizations
ABBREVIATIONS = [
    (r"\bsh\b", "show"),
    (r"\bint\b", "interface"),
    (r"\bgi(?=[0-9]|\b)", "gigabitethernet"),
    (r"\bfa(?=[0-9]|\b)", "fastethernet"),
    (r"\bte(?=[0-9]|\b)", "tengigabitethernet"),
    (r"\bpo(?=[0-9]|\b)", "port-channel"),
    (r"\bsw\b", "switchport"),
    (r"\bmo\b", "mode"),
    (r"\btr\b", "trunk"),
    (r"\bac\b", "access"),
    (r"\bno\s+shut\b", "no shutdown"),
    (r"\bip\s+add\b", "ip address"),
    (r"\brouter\s+ospf\b", "router ospf"),
    (r"\bnet\b", "network"),
    (r"\bconf\s+t\b", "configure terminal"),
    (r"\bdo\s+sh\b", "show"),
    (r"\bdesc\b", "description"),
    (r"\bencap\b", "encapsulation"),
    (r"\bdot1q\b", "dot1q"),
    (r"\bnat\b", "nat"),
    (r"\btrans\b", "translations"),
    (r"\bacc\b", "access-list"),
    (r"\bacl\b", "access-list"),
    (r"\bperm\b", "permit"),
    (r"\bstd\b", "standby"),
    (r"\bprio\b", "priority"),
    (r"\bpre\b", "preempt"),
]


def normalize_cisco_line(line: str) -> str:
    """Normalizes a single Cisco IOS command line for consistent regex matching."""
    cleaned = line.strip()
    # Remove CLI prompts like Router#, Switch(config-if)#, SW1>
    cleaned = re.sub(r'^[A-Za-z0-9_\-\.\(\)]+[#>]', '', cleaned).strip()
    # Remove leading comment markers
    cleaned = re.sub(r'^[!#]+\s*', '', cleaned).strip()
    lower = cleaned.lower()

    # Apply abbreviation expansions
    for pattern, replacement in ABBREVIATIONS:
        lower = re.sub(pattern, replacement, lower)

    # Collapse multiple whitespace
    lower = re.sub(r'\s+', ' ', lower).strip()
    return lower


def extract_cisco_sections(config_text: str) -> Dict[str, List[str]]:
    """Parses Cisco IOS running-config into hierarchical blocks (global, interface, router, vlan, etc.)."""
    sections: Dict[str, List[str]] = {"global": []}
    current_section = "global"

    for raw_line in config_text.splitlines():
        line = normalize_cisco_line(raw_line)
        if not line:
            continue

        # Detect section headers
        is_header = False
        if line.startswith("interface "):
            current_section = line
            is_header = True
        elif line.startswith("router "):
            current_section = line
            is_header = True
        elif line.startswith("vlan ") and len(line.split()) == 2 and line.split()[1].isdigit():
            current_section = line
            is_header = True
        elif line.startswith("line ") or line.startswith("ip dhcp pool "):
            current_section = line
            is_header = True
        elif line == "exit" or line == "end" or raw_line.strip() == "!":
            current_section = "global"
            continue

        sections.setdefault(current_section, [])
        sections[current_section].append(line)
        sections["global"].append(line)

    return sections


def grade_cisco_config(
    submitted_text: str,
    expected_rules: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Evaluates candidate submitted Cisco configuration or show output against lab rules.
    Returns score (0-100), passed_rules, missing_rules, and line diagnostics.
    """
    if not submitted_text or not submitted_text.strip():
        return {
            "score": 0,
            "passed": False,
            "total_rules": len(expected_rules),
            "passed_count": 0,
            "passed_rules": [],
            "missing_rules": [
                {
                    "description": r.get("description", "Configuration requirement"),
                    "help_tip": r.get("help_tip", "Please paste your running-config or show command output.")
                }
                for r in expected_rules
            ],
            "line_diagnostics": [],
            "summary": "No configuration was submitted. Paste your Cisco IOS config to check."
        }

    sections = extract_cisco_sections(submitted_text)
    all_normalized_lines = sections.get("global", [])
    full_text_normalized = "\n".join(all_normalized_lines)

    passed_rules: List[str] = []
    missing_rules: List[Dict[str, str]] = []
    total_weight = 0
    earned_weight = 0

    for rule in expected_rules:
        pattern = rule.get("pattern", "")
        neg_pattern = rule.get("negative_pattern")
        target_section = rule.get("section")
        description = rule.get("description", "Rule")
        help_tip = rule.get("help_tip", "Check Cisco command syntax.")
        weight = int(rule.get("weight", 1))
        total_weight += weight

        # Determine target text to search
        search_corpus = full_text_normalized
        if target_section:
            norm_target = normalize_cisco_line(target_section)
            # Find closest matching section key
            matching_sec_lines = []
            for sec_key, sec_lines in sections.items():
                if norm_target in sec_key or sec_key in norm_target:
                    matching_sec_lines.extend(sec_lines)
            if matching_sec_lines:
                search_corpus = "\n".join(matching_sec_lines)

        # Check positive regex match
        matched = False
        if pattern:
            matched = bool(re.search(pattern, search_corpus, re.IGNORECASE))

        # Check negative pattern (if something should NOT be present)
        if matched and neg_pattern:
            if re.search(neg_pattern, search_corpus, re.IGNORECASE):
                matched = False

        if matched:
            passed_rules.append(description)
            earned_weight += weight
        else:
            missing_rules.append({
                "description": description,
                "help_tip": help_tip,
                "section": target_section or "global"
            })

    total_rules = len(expected_rules)
    score = round((earned_weight / total_weight) * 100) if total_weight > 0 else 100
    is_passed = score >= 80

    # Generate line diagnostics for visual terminal feedback
    line_diagnostics = []
    for raw_line in submitted_text.splitlines()[:100]:
        cleaned = raw_line.strip()
        if not cleaned:
            continue
        norm = normalize_cisco_line(cleaned)
        # Check if line matches any passed rule's pattern
        matches_rule = any(
            re.search(r.get("pattern", ""), norm, re.IGNORECASE)
            for r in expected_rules
            if r.get("pattern") and r.get("description") in passed_rules
        )
        line_diagnostics.append({
            "line": raw_line,
            "status": "correct" if matches_rule else "neutral"
        })

    summary = (
        f"Passed {len(passed_rules)} of {total_rules} objectives ({score}%). "
        f"{'Lab complete!' if is_passed else 'Review the missing directives below to achieve full credit.'}"
    )

    return {
        "score": score,
        "passed": is_passed,
        "total_rules": total_rules,
        "passed_count": len(passed_rules),
        "passed_rules": passed_rules,
        "missing_rules": missing_rules,
        "line_diagnostics": line_diagnostics,
        "summary": summary,
    }
