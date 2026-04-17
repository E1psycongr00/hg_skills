#!/usr/bin/env python3
"""Shared helpers for reading Agent Skill documents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import yaml


UTF8 = "utf-8"
FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)", re.DOTALL)
FENCE_RE = re.compile(r"^\s*(```|~~~)")


@dataclass
class SkillDocument:
    skill_dir: Path
    skill_md: Path
    content: str
    frontmatter: dict
    body: str

    @property
    def name(self) -> str:
        return self.frontmatter.get("name", "")

    @property
    def description(self) -> str:
        return self.frontmatter.get("description", "")


def load_skill_document(skill_dir: str | Path) -> SkillDocument:
    """Load SKILL.md, parse frontmatter, and return the split document."""
    directory = Path(skill_dir)
    skill_md = directory / "SKILL.md"
    if not skill_md.exists():
        raise ValueError("SKILL.md not found")

    content = skill_md.read_text(encoding=UTF8)
    if not content.startswith("---"):
        raise ValueError("No YAML frontmatter found")

    frontmatter_match = FRONTMATTER_RE.match(content)
    if not frontmatter_match:
        raise ValueError("Invalid frontmatter format")

    try:
        frontmatter = yaml.safe_load(frontmatter_match.group(1))
    except yaml.YAMLError as error:
        raise ValueError(f"Invalid YAML in frontmatter: {error}") from error

    if not isinstance(frontmatter, dict):
        raise ValueError("Frontmatter must be a YAML dictionary")

    body = content[frontmatter_match.end():].lstrip("\r\n")
    return SkillDocument(
        skill_dir=directory,
        skill_md=skill_md,
        content=content,
        frontmatter=frontmatter,
        body=body,
    )


def iter_non_code_lines(text: str):
    """Yield non-code lines while skipping fenced code blocks."""
    in_fenced_code_block = False

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if FENCE_RE.match(raw_line):
            in_fenced_code_block = not in_fenced_code_block
            continue

        if in_fenced_code_block:
            continue

        yield line_number, raw_line


def count_nonempty_noncode_lines(text: str) -> int:
    """Count non-empty lines outside fenced code blocks."""
    count = 0
    for _, raw_line in iter_non_code_lines(text):
        if raw_line.strip():
            count += 1
    return count


def extract_markdown_headings(text: str):
    """Return markdown headings outside fenced code blocks."""
    headings = []
    for line_number, raw_line in iter_non_code_lines(text):
        stripped = raw_line.strip()
        if not stripped.startswith("#"):
            continue

        heading = re.sub(r"^#{1,6}\s*", "", stripped).strip()
        if heading:
            headings.append((line_number, heading))

    return headings

