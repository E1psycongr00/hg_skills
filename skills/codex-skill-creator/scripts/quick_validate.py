#!/usr/bin/env python3
"""
Quick validation script for skills - minimal version
"""

import sys
import re
import yaml
from pathlib import Path


UTF8 = "utf-8"
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
RESOURCE_HINT_PATTERNS = (
    re.compile(r"`(?:references|scripts|assets)/`"),
    re.compile(r"(?i)\b(?:references|scripts|assets)/"),
    re.compile(r"참조\s*(?:파일|문서)"),
    re.compile(r"출력\s*템플릿"),
    re.compile(r"스크립트"),
)
FALLBACK_HINT_PATTERNS = (
    re.compile(r"(?i)\bfallback\b"),
    re.compile(r"실패\s*시"),
    re.compile(r"없(?:으면|을\s*때)"),
    re.compile(r"미가용"),
    re.compile(r"차단\s*요인"),
    re.compile(r"중단"),
    re.compile(r"보고"),
)
FINAL_CHECK_HINT_PATTERNS = (
    re.compile(r"최종\s*점검"),
    re.compile(r"마지막\s*확인"),
    re.compile(r"체크리스트"),
    re.compile(r"점검"),
    re.compile(r"검증"),
    re.compile(r"(?i)\bfinal\s+check\b"),
    re.compile(r"(?i)\breview\b"),
)
HEADING_TRIGGER_PATTERN = re.compile(
    r"(?i)^#{1,6}\s*"
    r"(?:"
    r"언제\s*(?:사용|써야)|"
    r"사용\s*범위|"
    r"트리거(?:\s*조건|\s*기준)?|"
    r"언제\s*트리거(?:되고|되는지)?|"
    r"usage\s*scope|"
    r"when\s+to\s+use|"
    r"when\s+not\s+to\s+use|"
    r"should\s+trigger|"
    r"should\s+not\s+trigger|"
    r"do\s+not\s+use(?:\s+this\s+skill)?|"
    r"trigger\s*(?:conditions?|rules?|guidance)"
    r")\b"
)
LIST_TRIGGER_PATTERN = re.compile(
    r"(?i)^"
    r"(?:[-*+]\s*|\d+[.)]\s*)?"
    r"(?:\*\*|__)?\s*"
    r"(?:"
    r"언제\s*(?:사용|써야)|"
    r"사용\s*범위|"
    r"트리거(?:\s*조건|\s*기준)?|"
    r"언제\s*트리거(?:되고|되는지)?|"
    r"usage\s*scope|"
    r"when\s+to\s+use|"
    r"when\s+not\s+to\s+use|"
    r"should\s+trigger|"
    r"should\s+not\s+trigger|"
    r"do\s+not\s+use(?:\s+this\s+skill)?|"
    r"trigger\s*(?:conditions?|rules?|guidance)"
    r")"
    r"(?:\s*(?:\*\*|__))?"
    r"(?=\s*(?::|-|$))"
)
BODY_TRIGGER_PATTERNS = (
    HEADING_TRIGGER_PATTERN,
    LIST_TRIGGER_PATTERN,
    re.compile(
        r"(?i)^(?:[-*+]\s*|\d+[.)]\s*)?"
        r"use\s+this\s+skill\s+when\b"
    ),
    re.compile(
        r"(?i)^(?:[-*+]\s*|\d+[.)]\s*)?"
        r"do\s+not\s+use\s+this\s+skill\s+when\b"
    ),
    re.compile(
        r"(?i)^(?:[-*+]\s*|\d+[.)]\s*)?"
        r"this\s+skill\s+should(?:\s+not)?\s+trigger\b"
    ),
    re.compile(
        r"(?im)^(?:[-*+]\s*|\d+[.)]\s*)?"
        r"이\s*스킬(?:은|을)\s+.*(?:때|경우).*(?:사용(?:하세요|합니다|한다)|써야\s*한다)\b"
    ),
    re.compile(
        r"(?im)^(?:[-*+]\s*|\d+[.)]\s*)?"
        r"이\s*스킬(?:은|을)\s+.*(?:때|경우).*(?:사용하지\s*마세요|사용하면\s*안\s*된다|쓰지\s*마세요)\b"
    ),
)


def normalize_body_line(line):
    """Remove inline code and collapse spacing for line-by-line trigger scans."""
    without_inline_code = INLINE_CODE_RE.sub("", line)
    return " ".join(without_inline_code.split())


def iter_non_code_body_lines(body_text):
    """Yield body lines while skipping fenced code blocks."""
    in_fenced_code_block = False

    for line_number, raw_line in enumerate(body_text.splitlines(), start=1):
        if raw_line.lstrip().startswith("```"):
            in_fenced_code_block = not in_fenced_code_block
            continue

        if in_fenced_code_block:
            continue

        yield line_number, raw_line


def find_trigger_leakage(body_text):
    """Return the first trigger-style body snippet that should live in description."""
    for line_number, raw_line in iter_non_code_body_lines(body_text):
        normalized_line = normalize_body_line(raw_line)
        if not normalized_line:
            continue

        for pattern in BODY_TRIGGER_PATTERNS:
            if pattern.search(normalized_line):
                return line_number, normalized_line

    return None


def collect_body_lines(body_text):
    """Return normalized non-empty body lines outside fenced code blocks."""
    lines = []

    for _, raw_line in iter_non_code_body_lines(body_text):
        normalized_line = normalize_body_line(raw_line)
        if normalized_line:
            lines.append(normalized_line)

    return lines


def body_has_any_hint(body_lines, patterns):
    """Return True when any normalized body line matches the provided patterns."""
    for line in body_lines:
        for pattern in patterns:
            if pattern.search(line):
                return True

    return False


def collect_soft_warnings(skill_path, content, body_text):
    """Return non-fatal guidance about maintainability and progressive disclosure."""
    warnings = []
    total_line_count = len(content.splitlines())
    body_lines = collect_body_lines(body_text)
    body_line_count = len(body_lines)

    if total_line_count > 400:
        warnings.append(
            "SKILL.md is over 400 lines. Consider moving detailed domain guidance into "
            "references/, deterministic steps into scripts/, or output formats into assets/."
        )
    elif body_line_count > 220:
        warnings.append(
            "SKILL.md body is getting long. Re-check whether detailed guidance can move to "
            "references/, scripts/, or assets/ before adding more prose."
        )

    resource_dirs_exist = any(
        (skill_path / directory_name).exists()
        for directory_name in ("references", "scripts", "assets")
    )
    has_resource_guidance = body_has_any_hint(body_lines, RESOURCE_HINT_PATTERNS)
    if body_line_count > 160 and resource_dirs_exist and not has_resource_guidance:
        warnings.append(
            "This skill has companion resources but the body does not clearly say when to read "
            "references/ or use scripts/assets. Consider adding a short routing hint."
        )

    has_fallback_guidance = body_has_any_hint(body_lines, FALLBACK_HINT_PATTERNS)
    if not has_fallback_guidance:
        warnings.append(
            "No obvious fallback guidance found in SKILL.md body. If tools, inputs, or context "
            "can be missing, consider adding a short non-rigid fallback/reporting rule."
        )

    has_final_check_guidance = body_has_any_hint(body_lines, FINAL_CHECK_HINT_PATTERNS)
    if not has_final_check_guidance:
        warnings.append(
            "No obvious final-check guidance found in SKILL.md body. Consider adding a short "
            "review or completion check before finishing work."
        )

    return warnings


def fail(message):
    """Return a validation failure with no soft warnings."""
    return False, message, []


def validate_skill(skill_path):
    """Basic validation of a skill"""
    skill_path = Path(skill_path)

    # Check SKILL.md exists
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return fail("SKILL.md not found")

    # Read and validate frontmatter
    content = skill_md.read_text(encoding=UTF8)
    if not content.startswith('---'):
        return fail("No YAML frontmatter found")

    # Extract frontmatter
    frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not frontmatter_match:
        return fail("Invalid frontmatter format")

    frontmatter_text = frontmatter_match.group(1)

    # Parse YAML frontmatter
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
        if not isinstance(frontmatter, dict):
            return fail("Frontmatter must be a YAML dictionary")
    except yaml.YAMLError as e:
        return fail(f"Invalid YAML in frontmatter: {e}")

    # Define allowed properties
    ALLOWED_PROPERTIES = {'name', 'description', 'license', 'allowed-tools', 'metadata', 'compatibility'}

    # Check for unexpected properties (excluding nested keys under metadata)
    unexpected_keys = set(frontmatter.keys()) - ALLOWED_PROPERTIES
    if unexpected_keys:
        return fail(
            f"Unexpected key(s) in SKILL.md frontmatter: {', '.join(sorted(unexpected_keys))}. "
            f"Allowed properties are: {', '.join(sorted(ALLOWED_PROPERTIES))}"
        )

    # Check required fields
    if 'name' not in frontmatter:
        return fail("Missing 'name' in frontmatter")
    if 'description' not in frontmatter:
        return fail("Missing 'description' in frontmatter")

    # Extract name for validation
    name = frontmatter.get('name', '')
    if not isinstance(name, str):
        return fail(f"Name must be a string, got {type(name).__name__}")
    name = name.strip()
    if not name:
        return fail("Name cannot be empty")

    # Check naming convention (kebab-case: lowercase with hyphens)
    if not re.match(r'^[a-z0-9-]+$', name):
        return fail(f"Name '{name}' should be kebab-case (lowercase letters, digits, and hyphens only)")
    if name.startswith('-') or name.endswith('-') or '--' in name:
        return fail(f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens")
    # Check name length (max 64 characters per spec)
    if len(name) > 64:
        return fail(f"Name is too long ({len(name)} characters). Maximum is 64 characters.")

    # Extract and validate description
    description = frontmatter.get('description', '')
    if not isinstance(description, str):
        return fail(f"Description must be a string, got {type(description).__name__}")
    description = description.strip()
    if not description:
        return fail("Description cannot be empty")

    # Check for angle brackets
    if '<' in description or '>' in description:
        return fail("Description cannot contain angle brackets (< or >)")
    # Check description length (max 1024 characters per spec)
    if len(description) > 1024:
        return fail(f"Description is too long ({len(description)} characters). Maximum is 1024 characters.")

    # Validate compatibility field if present (optional)
    compatibility = frontmatter.get('compatibility', '')
    if compatibility:
        if not isinstance(compatibility, str):
            return fail(f"Compatibility must be a string, got {type(compatibility).__name__}")
        if len(compatibility) > 500:
            return fail(f"Compatibility is too long ({len(compatibility)} characters). Maximum is 500 characters.")

    body = content[frontmatter_match.end():].strip()
    if not body:
        return fail("SKILL.md body is empty. Keep workflow guidance in the body, not only in frontmatter.")

    body_trigger_leak = find_trigger_leakage(body)
    if body_trigger_leak:
        line_number, snippet = body_trigger_leak
        return fail(
            "SKILL.md body appears to contain trigger guidance "
            f"on line {line_number} ('{snippet}'). Move when-to-use / when-not-to-use rules "
            "into the frontmatter description and keep the body focused on workflow."
        )

    warnings = collect_soft_warnings(skill_path, content, body)
    return True, "Skill is valid!", warnings

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_validate.py <skill_directory>")
        sys.exit(1)
    
    valid, message, warnings = validate_skill(sys.argv[1])
    print(message)
    if warnings:
        print()
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
    sys.exit(0 if valid else 1)
