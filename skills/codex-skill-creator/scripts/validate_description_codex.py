#!/usr/bin/env python3
"""Fast Codex-based validator for skill descriptions."""

from __future__ import annotations

import argparse
import json
import sys
import textwrap

from codex_exec_utils import load_skill_for_codex, print_codex_result, run_codex_json_check


DEFAULT_MODEL = "gpt-5.4-mini"
DEFAULT_REASONING_EFFORT = "high"


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Use codex exec in ephemeral mode to quickly judge whether a skill description "
            "acts like routing metadata rather than execution instructions. "
            f"Defaults: model={DEFAULT_MODEL}, reasoning={DEFAULT_REASONING_EFFORT}."
        )
    )
    parser.add_argument("skill_directory", help="Path to the skill directory")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Codex model override (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--reasoning-effort",
        default=DEFAULT_REASONING_EFFORT,
        help=f"Codex reasoning effort override (default: {DEFAULT_REASONING_EFFORT})",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=90,
        help="Timeout for the codex exec call (default: 90)",
    )
    parser.add_argument("--json", action="store_true", help="Print the result as JSON")
    return parser


def build_prompt(skill_name: str, description: str) -> str:
    """Build the validation prompt."""
    return textwrap.dedent(
        f"""
        You are doing a fast review of an Agent Skill frontmatter description.

        Goal:
        - Judge whether the description is serving the right role.

        Pass when:
        - It mainly tells the agent what the skill does and when to use it.
        - It stays at routing-metadata level.

        Warn when:
        - It partly drifts into internal process, workflow, or implementation detail.
        - It is too vague to trigger reliably.

        Fail only when:
        - It is mostly operational guidance that belongs in the SKILL.md body.
        - It mainly describes step order, scope-management rules, tool choreography, or validation procedure.

        Important:
        - Do not nitpick isolated keywords.
        - Judge the overall meaning in context.
        - Keep the review short and high-signal.
        - Leave suggested_rewrite empty on pass.

        Skill name: {skill_name}
        Description:
        {description}
        """
    ).strip()


def main(argv: list[str] | None = None) -> int:
    """Run the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    document = load_skill_for_codex(args.skill_directory)
    prompt = build_prompt(document.name, document.description)
    result = run_codex_json_check(
        prompt,
        cwd=document.skill_dir,
        model=args.model,
        reasoning_effort=args.reasoning_effort,
        timeout_seconds=args.timeout_seconds,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_codex_result(result)

    return 0 if result.get("verdict") != "fail" else 1


if __name__ == "__main__":
    sys.exit(main())
