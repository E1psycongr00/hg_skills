"""Shared utilities for codex-skill-creator scripts."""

from pathlib import Path

UTF8 = "utf-8"
ALLOWED_REASONING_EFFORTS = ("low", "medium", "high", "xhigh")
DEFAULT_MINI_REASONING_EFFORT = "high"


def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    """Parse a SKILL.md file, returning (name, description, full_content)."""
    content = (skill_path / "SKILL.md").read_text(encoding=UTF8)
    lines = content.split("\n")

    if lines[0].strip() != "---":
        raise ValueError("SKILL.md missing frontmatter (no opening ---)")

    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        raise ValueError("SKILL.md missing frontmatter (no closing ---)")

    name = ""
    description = ""
    frontmatter_lines = lines[1:end_idx]
    i = 0
    while i < len(frontmatter_lines):
        line = frontmatter_lines[i]
        if line.startswith("name:"):
            name = line[len("name:"):].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            value = line[len("description:"):].strip()
            # Handle YAML multiline indicators (>, |, >-, |-)
            if value in (">", "|", ">-", "|-"):
                continuation_lines: list[str] = []
                i += 1
                while i < len(frontmatter_lines) and (frontmatter_lines[i].startswith("  ") or frontmatter_lines[i].startswith("\t")):
                    continuation_lines.append(frontmatter_lines[i].strip())
                    i += 1
                description = " ".join(continuation_lines)
                continue
            else:
                description = value.strip('"').strip("'")
        i += 1

    return name, description, content


def resolve_reasoning_effort(model: str | None, reasoning_effort: str | None) -> str | None:
    """Resolve the Codex reasoning effort, defaulting gpt-5.4-mini to high."""
    if reasoning_effort:
        normalized = reasoning_effort.strip().lower()
        if normalized not in ALLOWED_REASONING_EFFORTS:
            allowed = ", ".join(ALLOWED_REASONING_EFFORTS)
            raise ValueError(f"Unsupported reasoning effort '{reasoning_effort}'. Expected one of: {allowed}")
        return normalized

    if model and model.strip().lower() == "gpt-5.4-mini":
        return DEFAULT_MINI_REASONING_EFFORT

    return None


def apply_codex_model_settings(cmd: list[str], model: str | None, reasoning_effort: str | None) -> str | None:
    """Append model-related Codex CLI args and return the resolved reasoning effort."""
    if model:
        cmd.extend(["--model", model])

    resolved_reasoning_effort = resolve_reasoning_effort(model, reasoning_effort)
    if resolved_reasoning_effort:
        cmd.extend(["-c", f'model_reasoning_effort="{resolved_reasoning_effort}"'])

    return resolved_reasoning_effort
