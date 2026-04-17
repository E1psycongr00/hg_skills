#!/usr/bin/env python3
"""Helpers for fast Codex-based skill content validation."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from skill_document import UTF8, load_skill_document


DEFAULT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["verdict", "summary", "issues", "suggested_rewrite", "suggested_action"],
    "properties": {
        "verdict": {
            "type": "string",
            "enum": ["pass", "warn", "fail"],
        },
        "summary": {
            "type": "string",
            "minLength": 1,
            "maxLength": 240,
        },
        "issues": {
            "type": "array",
            "items": {
                "type": "string",
                "minLength": 1,
                "maxLength": 240,
            },
            "maxItems": 3,
        },
        "suggested_rewrite": {
            "type": "string",
            "maxLength": 500,
        },
        "suggested_action": {
            "type": "string",
            "maxLength": 500,
        },
    },
}


def summarize_process_output(text: str, max_lines: int = 40, max_chars: int = 4000) -> str:
    """Trim noisy Codex CLI stderr/stdout down to the most useful lines."""
    stripped = text.strip()
    if not stripped:
        return "(empty)"

    filtered_lines = []
    for line in stripped.splitlines():
        compact = line.strip()
        if not compact:
            continue
        if compact.startswith("<") and compact.endswith(">"):
            continue
        if "remote plugin sync request" in compact:
            continue
        if "/cdn-cgi/challenge-platform/" in compact:
            continue
        filtered_lines.append(line)

    lines = filtered_lines or stripped.splitlines()
    snippet = "\n".join(lines[-max_lines:])
    if len(snippet) > max_chars:
        snippet = "...\n" + snippet[-max_chars:]
    return snippet


def truncate_text(text: str, max_chars: int) -> str:
    """Keep prompts compact without losing both the front and back of a long body."""
    if max_chars <= 0 or len(text) <= max_chars:
        return text

    head = max_chars // 2
    tail = max_chars - head
    return (
        text[:head].rstrip()
        + "\n\n...[truncated for fast validation]...\n\n"
        + text[-tail:].lstrip()
    )


def run_codex_json_check(
    prompt: str,
    cwd: str | Path,
    model: str | None = None,
    reasoning_effort: str | None = None,
    timeout_seconds: int = 90,
    schema: dict | None = None,
) -> dict:
    """Run a one-shot Codex exec validation and return parsed JSON."""
    working_directory = Path(cwd)
    response_schema = schema or DEFAULT_SCHEMA

    with tempfile.TemporaryDirectory(prefix="codex-skill-check-") as temp_dir:
        temp_path = Path(temp_dir)
        schema_path = temp_path / "schema.json"
        output_path = temp_path / "output.json"
        schema_path.write_text(json.dumps(response_schema, ensure_ascii=False, indent=2), encoding=UTF8)

        command = [
            "codex",
            "exec",
            "--ephemeral",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
            "--color",
            "never",
            "-C",
            str(working_directory),
            "--output-schema",
            str(schema_path),
            "-o",
            str(output_path),
            "-",
        ]
        if model:
            command.extend(["-m", model])
        if reasoning_effort:
            command.extend(["-c", f'model_reasoning_effort="{reasoning_effort}"'])

        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            encoding=UTF8,
            timeout=timeout_seconds,
            check=False,
        )

        if completed.returncode != 0:
            stderr = summarize_process_output(completed.stderr)
            stdout = summarize_process_output(completed.stdout)
            raise RuntimeError(
                "codex exec failed with return code "
                f"{completed.returncode}.\nSTDERR:\n{stderr or '(empty)'}\nSTDOUT:\n{stdout or '(empty)'}"
            )

        if not output_path.exists():
            raise RuntimeError("codex exec completed without writing the structured output file.")

        try:
            return json.loads(output_path.read_text(encoding=UTF8))
        except json.JSONDecodeError as error:
            raise RuntimeError(f"Could not parse codex JSON output: {error}") from error


def load_skill_for_codex(skill_dir: str | Path):
    """Load a skill document for Codex-driven validation."""
    return load_skill_document(skill_dir)


def print_codex_result(result: dict) -> None:
    """Print a compact human-readable report."""
    verdict = result.get("verdict", "warn").upper()
    print(f"Verdict: {verdict}")
    print(result.get("summary", ""))

    issues = result.get("issues", [])
    if issues:
        print()
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")

    suggested_rewrite = result.get("suggested_rewrite", "").strip()
    if suggested_rewrite:
        print()
        print("Suggested Rewrite:")
        print(suggested_rewrite)

    suggested_action = result.get("suggested_action", "").strip()
    if suggested_action:
        print()
        print("Suggested Action:")
        print(suggested_action)
