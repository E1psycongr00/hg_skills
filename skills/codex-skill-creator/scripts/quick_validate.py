#!/usr/bin/env python3
"""Fast structural validator for Agent Skills."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from skill_document import (
    count_nonempty_noncode_lines,
    extract_markdown_headings,
    load_skill_document,
)


ALLOWED_PROPERTIES = {
    "name",
    "description",
    "license",
    "allowed-tools",
    "metadata",
    "compatibility",
}
RESOURCE_DIRECTORIES = ("references", "scripts", "assets", "evals")
BANNED_TRIGGER_HEADINGS = (
    re.compile(r"(?i)^when to use$"),
    re.compile(r"(?i)^when not to use$"),
    re.compile(r"(?i)^usage scope$"),
    re.compile(r"(?i)^do not use(?: this skill)?$"),
    re.compile(r"(?i)^should trigger$"),
    re.compile(r"(?i)^should not trigger$"),
    re.compile(r"(?i)^trigger conditions?$"),
    re.compile(r"(?i)^trigger rules?$"),
    re.compile(r"^언제\s*(?:사용|써야)$"),
    re.compile(r"^사용\s*범위$"),
    re.compile(r"^트리거\s*(?:조건|기준)$"),
)


@dataclass
class ValidationResult:
    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.valid = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)


def normalize_heading(heading: str) -> str:
    """Normalize markdown heading text for exact structural checks."""
    without_markup = re.sub(r"[`*_]", "", heading)
    return " ".join(without_markup.split()).strip()


def find_banned_trigger_heading(body: str):
    """Return the first trigger-only heading found in the body."""
    for line_number, heading in extract_markdown_headings(body):
        normalized = normalize_heading(heading)
        for pattern in BANNED_TRIGGER_HEADINGS:
            if pattern.fullmatch(normalized):
                return line_number, heading
    return None


def validate_skill(skill_path: str | Path) -> ValidationResult:
    """Validate structural properties of a skill directory."""
    result = ValidationResult()

    try:
        document = load_skill_document(skill_path)
    except ValueError as error:
        result.add_error(str(error))
        return result

    frontmatter = document.frontmatter

    unexpected_keys = sorted(set(frontmatter.keys()) - ALLOWED_PROPERTIES)
    if unexpected_keys:
        result.add_error(
            "Unexpected key(s) in SKILL.md frontmatter: "
            f"{', '.join(unexpected_keys)}. Allowed properties are: "
            f"{', '.join(sorted(ALLOWED_PROPERTIES))}"
        )

    if "name" not in frontmatter:
        result.add_error("Missing 'name' in frontmatter")
    if "description" not in frontmatter:
        result.add_error("Missing 'description' in frontmatter")

    name = frontmatter.get("name", "")
    if not isinstance(name, str):
        result.add_error(f"Name must be a string, got {type(name).__name__}")
    else:
        stripped_name = name.strip()
        if not stripped_name:
            result.add_error("Name cannot be empty")
        elif not re.match(r"^[a-z0-9-]+$", stripped_name):
            result.add_error(
                f"Name '{stripped_name}' should be kebab-case "
                "(lowercase letters, digits, and hyphens only)"
            )
        elif stripped_name.startswith("-") or stripped_name.endswith("-") or "--" in stripped_name:
            result.add_error(
                f"Name '{stripped_name}' cannot start/end with hyphen or contain consecutive hyphens"
            )
        elif len(stripped_name) > 64:
            result.add_error(f"Name is too long ({len(stripped_name)} characters). Maximum is 64 characters.")
        elif stripped_name != document.skill_dir.name:
            result.add_error(
                f"Name '{stripped_name}' must match the parent directory name '{document.skill_dir.name}'."
            )

    description = frontmatter.get("description", "")
    if not isinstance(description, str):
        result.add_error(f"Description must be a string, got {type(description).__name__}")
    else:
        stripped_description = description.strip()
        if not stripped_description:
            result.add_error("Description cannot be empty")
        elif "<" in stripped_description or ">" in stripped_description:
            result.add_error("Description cannot contain angle brackets (< or >)")
        elif len(stripped_description) > 1024:
            result.add_error(
                f"Description is too long ({len(stripped_description)} characters). Maximum is 1024 characters."
            )
        elif len(stripped_description) > 320:
            result.add_warning(
                "Description is getting long. Re-check whether it still reads like compact routing metadata."
            )

    compatibility = frontmatter.get("compatibility", "")
    if compatibility:
        if not isinstance(compatibility, str):
            result.add_error(f"Compatibility must be a string, got {type(compatibility).__name__}")
        elif len(compatibility) > 500:
            result.add_error(
                f"Compatibility is too long ({len(compatibility)} characters). Maximum is 500 characters."
            )

    if not document.body.strip():
        result.add_error("SKILL.md body is empty. Keep workflow guidance in the body, not only in frontmatter.")
        return result

    banned_heading = find_banned_trigger_heading(document.body)
    if banned_heading:
        line_number, heading = banned_heading
        result.add_error(
            "SKILL.md body contains a trigger-only heading "
            f"on line {line_number} ('{heading}'). Keep trigger selection in description and "
            "use the body for after-activation workflow guidance."
        )

    total_line_count = len(document.content.splitlines())
    body_line_count = count_nonempty_noncode_lines(document.body)
    heading_count = len(extract_markdown_headings(document.body))

    if total_line_count > 400:
        result.add_warning(
            "SKILL.md is over 400 lines. Consider moving detailed variants into references/, "
            "deterministic execution into scripts/, or repeated output formats into assets/."
        )
    if body_line_count > 260:
        result.add_warning(
            "SKILL.md body is getting long. Re-check whether structural detail belongs in references/, "
            "scripts/, or assets/."
        )
    if heading_count == 0 and body_line_count > 120:
        result.add_warning(
            "Long body with no markdown headings found. Consider adding section structure for readability."
        )

    for directory_name in RESOURCE_DIRECTORIES:
        resource_path = document.skill_dir / directory_name
        if resource_path.exists() and not resource_path.is_dir():
            result.add_error(f"'{directory_name}' exists but is not a directory.")
        elif resource_path.is_dir():
            has_visible_children = any(
                child.name not in {".gitkeep", ".keep"} for child in resource_path.iterdir()
            )
            if not has_visible_children:
                result.add_warning(f"'{directory_name}/' exists but appears to be empty.")

    return result


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser."""
    parser = argparse.ArgumentParser(
        description="Fast structural validator for Agent Skills. This checks format and layout, not semantic quality."
    )
    parser.add_argument("skill_directory", help="Path to the skill directory")
    parser.add_argument("--json", action="store_true", help="Print the result as JSON")
    return parser


def print_human_result(result: ValidationResult) -> None:
    """Render validation output for humans."""
    if result.valid:
        print("Skill structure is valid!")
    else:
        print("Skill structure is invalid.")

    if result.errors:
        print()
        print("Errors:")
        for error in result.errors:
            print(f"- {error}")

    if result.warnings:
        print()
        print("Warnings:")
        for warning in result.warnings:
            print(f"- {warning}")


def main(argv: list[str] | None = None) -> int:
    """Run the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    result = validate_skill(args.skill_directory)

    if args.json:
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    else:
        print_human_result(result)

    return 0 if result.valid else 1


if __name__ == "__main__":
    sys.exit(main())

