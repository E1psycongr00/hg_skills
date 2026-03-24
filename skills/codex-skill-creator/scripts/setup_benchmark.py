#!/usr/bin/env python3
"""
Prepare benchmark workspace scaffolding for a skill.

This script reads `evals/evals.json` from a skill directory and creates the
iteration/eval/config/run structure expected by aggregate_benchmark.py.

Usage:
    python -m scripts.setup_benchmark path/to/skill
    python -m scripts.setup_benchmark path/to/skill --workspace-root ./tmp
    python -m scripts.setup_benchmark path/to/skill --iteration 2 --runs 2
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.utils import parse_skill_md
except ModuleNotFoundError:
    from utils import parse_skill_md


UTF8 = "utf-8"
MAX_RUNS = 3
EXCLUDED_DIRS = {"__pycache__", "node_modules"}
EXCLUDED_FILES = {".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc"}


def read_json_utf8(path: Path) -> dict:
    with path.open(encoding=UTF8) as handle:
        return json.load(handle)


def write_json_utf8(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding=UTF8) as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def write_text_utf8(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=UTF8)


def slugify(text: str, fallback: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    if not normalized:
        return fallback
    return normalized[:64]


def validate_runs(runs: int) -> int:
    if runs < 1 or runs > MAX_RUNS:
        raise ValueError(f"runs must be between 1 and {MAX_RUNS}")
    return runs


def next_iteration_number(workspace_root: Path) -> int:
    numbers: list[int] = []
    for iteration_dir in workspace_root.glob("iteration-*"):
        if not iteration_dir.is_dir():
            continue
        try:
            numbers.append(int(iteration_dir.name.split("-", 1)[1]))
        except (IndexError, ValueError):
            continue
    return max(numbers, default=0) + 1


def should_skip_copy(path: Path, skill_root: Path) -> bool:
    rel_path = path.relative_to(skill_root)
    if not rel_path.parts:
        return False
    if rel_path.parts[0] == "evals":
        return True
    if any(part in EXCLUDED_DIRS for part in rel_path.parts):
        return True
    if path.name in EXCLUDED_FILES:
        return True
    if path.suffix in EXCLUDED_SUFFIXES:
        return True
    return False


def copy_skill_bundle(source: Path, destination: Path) -> None:
    for item in source.rglob("*"):
        if item.is_dir():
            continue
        if should_skip_copy(item, source):
            continue
        relative_path = item.relative_to(source)
        target_path = destination / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target_path)


def stage_input_files(skill_path: Path, eval_dir: Path, files: list[str]) -> list[Path]:
    staged_paths: list[Path] = []
    for file_entry in files:
        rel_path = Path(file_entry)
        if rel_path.is_absolute():
            raise ValueError(f"Input files must be relative to the skill root: {file_entry}")

        source_path = (skill_path / rel_path).resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"Input file not found: {file_entry}")
        if not source_path.is_file():
            raise ValueError(f"Input path must be a file: {file_entry}")

        staged_path = eval_dir / "inputs" / rel_path
        staged_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, staged_path)
        staged_paths.append(staged_path)

    return staged_paths


def relative_posix_path(path: Path, start: Path) -> str:
    return Path(path.relative_to(start) if path.is_relative_to(start) else path).as_posix()


def relative_from(path: Path, start: Path) -> str:
    return Path(os.path.relpath(path, start)).as_posix()


def build_run_prompt(
    prompt: str,
    expected_output: str,
    staged_paths: list[Path],
    run_dir: Path,
) -> str:
    if staged_paths:
        input_block = "\n".join(
            f"  - `{relative_from(staged_path, run_dir)}`" for staged_path in staged_paths
        )
    else:
        input_block = '  - "none"'

    expected_output_line = expected_output or "사용자 요청에 맞는 최종 산출물"

    return "\n".join(
        [
            "다음 작업을 실행하세요.",
            "",
            f"- 작업: {prompt}",
            "- 입력 파일:",
            input_block,
            "- 출력 저장 위치: `outputs/`",
            f"- 기대 결과: {expected_output_line}",
            "- 실행 요약 저장 위치: `transcript.md`",
            "- 선택적 provenance 저장 위치: `run_provenance.json`",
            "",
            "추가 규칙:",
            "- 산출물은 지정된 `outputs/` 아래에 저장하세요.",
            "- 실행 중 참고한 핵심 파일, 사용한 스크립트, 남은 불확실성을 `transcript.md`에 짧게 정리하세요.",
            "- `run_provenance.json`을 쓴다면 `executor`, `configuration`, `baseline_type`, `skill_path_requested`, `prompt_path`, `command`를 기록하세요.",
        ]
    )


def load_evals(skill_path: Path, skill_name: str) -> list[dict]:
    evals_path = skill_path / "evals" / "evals.json"
    if not evals_path.exists():
        raise FileNotFoundError(f"evals.json not found: {evals_path}")

    payload = read_json_utf8(evals_path)
    payload_skill_name = payload.get("skill_name", "")
    if payload_skill_name and payload_skill_name != skill_name:
        raise ValueError(
            f"skill_name mismatch: SKILL.md='{skill_name}', evals.json='{payload_skill_name}'"
        )

    evals = payload.get("evals")
    if not isinstance(evals, list) or not evals:
        raise ValueError("evals.json must contain a non-empty 'evals' array")

    seen_ids: set[int] = set()
    normalized: list[dict] = []

    for index, raw_eval in enumerate(evals):
        if not isinstance(raw_eval, dict):
            raise ValueError(f"eval entry #{index} must be an object")

        eval_id = raw_eval.get("id")
        prompt = raw_eval.get("prompt")
        if not isinstance(eval_id, int):
            raise ValueError(f"eval entry #{index} is missing integer 'id'")
        if eval_id in seen_ids:
            raise ValueError(f"duplicate eval id: {eval_id}")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"eval entry #{index} is missing non-empty 'prompt'")

        files = raw_eval.get("files", [])
        expectations = raw_eval.get("expectations", [])
        expected_output = raw_eval.get("expected_output", "")
        eval_name = raw_eval.get("eval_name") or raw_eval.get("name")

        if not isinstance(files, list) or any(not isinstance(item, str) for item in files):
            raise ValueError(f"eval {eval_id} has invalid 'files'; expected a string array")
        if not isinstance(expectations, list) or any(not isinstance(item, str) for item in expectations):
            raise ValueError(f"eval {eval_id} has invalid 'expectations'; expected a string array")
        if expected_output and not isinstance(expected_output, str):
            raise ValueError(f"eval {eval_id} has invalid 'expected_output'; expected a string")
        if eval_name and not isinstance(eval_name, str):
            raise ValueError(f"eval {eval_id} has invalid 'eval_name'; expected a string")

        seen_ids.add(eval_id)
        normalized.append(
            {
                "id": eval_id,
                "prompt": prompt.strip(),
                "expected_output": expected_output.strip(),
                "files": files,
                "expectations": expectations,
                "eval_name": (eval_name or "").strip(),
            }
        )

    return normalized


def create_iteration_metadata(
    skill_name: str,
    skill_path: Path,
    workspace_root: Path,
    iteration_dir: Path,
    baseline: str,
    runs: int,
    evals: list[dict],
) -> dict:
    return {
        "skill_name": skill_name,
        "skill_path": str(skill_path),
        "workspace_root": str(workspace_root),
        "iteration": iteration_dir.name,
        "baseline": baseline,
        "runs_per_configuration": runs,
        "eval_ids": [item["id"] for item in evals],
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def prepare_benchmark_workspace(
    skill_path: Path,
    workspace_root: Path | None,
    iteration: int | None,
    runs: int,
    baseline: str,
    old_skill_path: Path | None,
) -> Path:
    skill_name, _, _ = parse_skill_md(skill_path)
    if not skill_name:
        raise ValueError("Unable to determine skill name from SKILL.md")

    evals = load_evals(skill_path, skill_name)
    workspace_root = (workspace_root or (skill_path.parent / f"{skill_name}-workspace")).resolve()
    workspace_root.mkdir(parents=True, exist_ok=True)

    iteration_number = iteration or next_iteration_number(workspace_root)
    iteration_dir = workspace_root / f"iteration-{iteration_number}"
    if iteration_dir.exists():
        raise FileExistsError(f"Iteration directory already exists: {iteration_dir}")

    if baseline == "old_skill" and old_skill_path is None:
        raise ValueError("--old-skill-path is required when baseline is 'old_skill'")

    if old_skill_path is not None:
        old_skill_path = old_skill_path.resolve()
        if not old_skill_path.exists():
            raise FileNotFoundError(f"Old skill path not found: {old_skill_path}")

    baseline_source = old_skill_path if baseline == "old_skill" else None
    config_order = ["with_skill", baseline]

    iteration_dir.mkdir(parents=True, exist_ok=False)
    write_json_utf8(
        iteration_dir / "iteration_metadata.json",
        create_iteration_metadata(
            skill_name=skill_name,
            skill_path=skill_path.resolve(),
            workspace_root=workspace_root,
            iteration_dir=iteration_dir,
            baseline=baseline,
            runs=runs,
            evals=evals,
        ),
    )

    for eval_case in evals:
        eval_dir = iteration_dir / f"eval-{eval_case['id']}"
        eval_dir.mkdir(parents=True, exist_ok=False)

        staged_inputs = stage_input_files(skill_path, eval_dir, eval_case["files"])
        eval_name = eval_case["eval_name"] or slugify(
            eval_case["expected_output"] or eval_case["prompt"],
            fallback=f"eval-{eval_case['id']}",
        )

        write_json_utf8(
            eval_dir / "eval_metadata.json",
            {
                "eval_id": eval_case["id"],
                "eval_name": eval_name,
                "prompt": eval_case["prompt"],
                "expected_output": eval_case["expected_output"],
                "files": eval_case["files"],
                "assertions": eval_case["expectations"],
                "staged_inputs": [
                    relative_posix_path(path, eval_dir) for path in staged_inputs
                ],
            },
        )

        for config_name in config_order:
            config_dir = eval_dir / config_name
            config_dir.mkdir(parents=True, exist_ok=True)

            for run_number in range(1, runs + 1):
                run_dir = config_dir / f"run-{run_number}"
                (run_dir / "outputs").mkdir(parents=True, exist_ok=True)

                run_prompt = build_run_prompt(
                    prompt=eval_case["prompt"],
                    expected_output=eval_case["expected_output"],
                    staged_paths=staged_inputs,
                    run_dir=run_dir,
                )
                write_text_utf8(run_dir / "run_prompt.md", run_prompt)

                if config_name == "with_skill":
                    copy_skill_bundle(
                        skill_path,
                        run_dir / ".agents" / "skills" / skill_path.name,
                    )
                elif config_name == "old_skill" and baseline_source is not None:
                    copy_skill_bundle(
                        baseline_source,
                        run_dir / ".agents" / "skills" / baseline_source.name,
                    )

    return iteration_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create benchmark workspace scaffolding from a skill's evals.json"
    )
    parser.add_argument(
        "skill_path",
        type=Path,
        help="Path to the benchmark target skill directory",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        help="Workspace root directory (default: sibling <skill-name>-workspace)",
    )
    parser.add_argument(
        "--iteration",
        type=int,
        help="Iteration number to create (default: next available iteration)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Runs to scaffold per config (default: 1, max: 3)",
    )
    parser.add_argument(
        "--baseline",
        choices=("without_skill", "old_skill"),
        default="without_skill",
        help="Baseline configuration to scaffold",
    )
    parser.add_argument(
        "--old-skill-path",
        type=Path,
        help="Snapshot skill path used when --baseline old_skill is selected",
    )

    args = parser.parse_args()

    try:
        runs = validate_runs(args.runs)
        iteration_dir = prepare_benchmark_workspace(
            skill_path=args.skill_path.resolve(),
            workspace_root=args.workspace_root.resolve() if args.workspace_root else None,
            iteration=args.iteration,
            runs=runs,
            baseline=args.baseline,
            old_skill_path=args.old_skill_path.resolve() if args.old_skill_path else None,
        )
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    print(f"Created benchmark scaffolding: {iteration_dir}")


if __name__ == "__main__":
    main()
