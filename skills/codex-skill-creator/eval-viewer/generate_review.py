#!/usr/bin/env python3
"""Generate and serve a review page for eval results.

Reads the workspace directory, discovers runs (directories with outputs/),
embeds all output data into a self-contained HTML page, and serves it via
a tiny HTTP server. Feedback auto-saves to feedback.json in the workspace.
Pass --static to write a standalone HTML file instead of starting a server.

Usage:
    python generate_review.py <workspace-path> [--port PORT] [--skill-name NAME]
    python generate_review.py <workspace-path> --static /path/to/review.html
    python generate_review.py <workspace-path> --previous-workspace /path/to/iteration-1

No dependencies beyond the Python stdlib are required.
"""

import argparse
import base64
import json
import mimetypes
import re
import sys
import webbrowser
from functools import partial
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

# Files to exclude from output listings
METADATA_FILES = {"transcript.md", "user_notes.md", "metrics.json"}

# Extensions we render as inline text
TEXT_EXTENSIONS = {
    ".txt", ".md", ".json", ".csv", ".py", ".js", ".ts", ".tsx", ".jsx",
    ".yaml", ".yml", ".xml", ".html", ".css", ".sh", ".rb", ".go", ".rs",
    ".java", ".c", ".cpp", ".h", ".hpp", ".sql", ".r", ".toml",
}

# Extensions we render as inline images
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}

# MIME type overrides for common types
MIME_OVERRIDES = {
    ".svg": "image/svg+xml",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


def read_text_utf8(path: Path, *, errors: str = "strict") -> str:
    return path.read_text(encoding="utf-8", errors=errors)


def read_json_utf8(path: Path) -> Any:
    return json.loads(read_text_utf8(path))


def write_text_utf8(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def iter_metadata_candidates(run_dir: Path, root: Path) -> list[Path]:
    candidates: list[Path] = []
    current = run_dir
    while True:
        candidates.append(current / "eval_metadata.json")
        if current == root:
            break
        if root not in current.parents:
            break
        current = current.parent
    return candidates


def collect_input_files(run_dir: Path, metadata_dir: Path, rel_paths: list[Any]) -> list[dict]:
    collected: list[dict] = []
    seen_names: set[str] = set()

    for rel_path in rel_paths:
        if not isinstance(rel_path, str):
            continue
        normalized = rel_path.replace("\\", "/")
        if normalized in seen_names:
            continue
        for file_candidate in [
            run_dir / rel_path,
            metadata_dir / rel_path,
        ]:
            if file_candidate.exists() and file_candidate.is_file():
                seen_names.add(normalized)
                collected.append(embed_file(file_candidate, display_name=normalized))
                break

    return collected


def json_for_script_tag(value: Any) -> str:
    """Serialize JSON so it is safe to embed inside a <script> tag."""
    return (
        json.dumps(value, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def get_mime_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in MIME_OVERRIDES:
        return MIME_OVERRIDES[ext]
    mime, _ = mimetypes.guess_type(str(path))
    return mime or "application/octet-stream"


def find_runs(workspace: Path) -> list[dict]:
    """Recursively find directories that contain an outputs/ subdirectory."""
    runs: list[dict] = []
    _find_runs_recursive(workspace, workspace, runs)
    runs.sort(key=lambda r: (r.get("eval_id", float("inf")), r["id"]))
    return runs


def _find_runs_recursive(root: Path, current: Path, runs: list[dict]) -> None:
    if not current.is_dir():
        return

    outputs_dir = current / "outputs"
    if outputs_dir.is_dir():
        run = build_run(root, current)
        if run:
            runs.append(run)
        return

    skip = {"node_modules", ".git", "__pycache__", "skill", "inputs"}
    for child in sorted(current.iterdir()):
        if child.is_dir() and child.name not in skip:
            _find_runs_recursive(root, child, runs)


def build_run(root: Path, run_dir: Path) -> dict | None:
    """Build a run dict with prompt, outputs, and grading data."""
    prompt = ""
    eval_id = None
    input_files: list[dict] = []

    # Try eval_metadata.json
    for candidate in iter_metadata_candidates(run_dir, root):
        if candidate.exists():
            try:
                metadata = read_json_utf8(candidate)
                prompt = metadata.get("prompt", "")
                eval_id = metadata.get("eval_id")
                input_files = collect_input_files(run_dir, candidate.parent, metadata.get("files", []))
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                pass
            if prompt:
                break

    # Fall back to transcript.md
    if not prompt:
        for candidate in [run_dir / "transcript.md", run_dir / "outputs" / "transcript.md"]:
            if candidate.exists():
                try:
                    text = read_text_utf8(candidate, errors="replace")
                    patterns = [
                        r"## Eval Prompt\n\n([\s\S]*?)(?=\n##|$)",
                        r"(?:^|\n)PROMPT\s*\n\s*\n([\s\S]*?)(?=\n\s*\n(?:STDOUT|STDERR)\b|$)",
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, text)
                        if match:
                            prompt = match.group(1).strip()
                            break
                except (OSError, UnicodeDecodeError):
                    pass
                if prompt:
                    break

    if not prompt:
        prompt = "(No prompt found)"

    run_id = str(run_dir.relative_to(root)).replace("/", "-").replace("\\", "-")

    # Collect output files
    outputs_dir = run_dir / "outputs"
    output_files: list[dict] = []
    if outputs_dir.is_dir():
        for f in sorted(outputs_dir.iterdir()):
            if f.is_file() and f.name not in METADATA_FILES:
                output_files.append(embed_file(f))

    # Load grading if present
    grading = None
    for candidate in [run_dir / "grading.json", run_dir.parent / "grading.json"]:
        if candidate.exists():
            try:
                grading = read_json_utf8(candidate)
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                pass
            if grading:
                break

    return {
        "id": run_id,
        "prompt": prompt,
        "eval_id": eval_id,
        "input_files": input_files,
        "outputs": output_files,
        "grading": grading,
    }


def embed_file(path: Path, *, display_name: str | None = None) -> dict:
    """Read a file and return an embedded representation."""
    ext = path.suffix.lower()
    mime = get_mime_type(path)
    name = display_name or path.name

    if ext in TEXT_EXTENSIONS:
        try:
            content = read_text_utf8(path, errors="replace")
        except (OSError, UnicodeDecodeError):
            content = "(Error reading file)"
        return {
            "name": name,
            "type": "text",
            "content": content,
        }
    elif ext in IMAGE_EXTENSIONS:
        try:
            raw = path.read_bytes()
            b64 = base64.b64encode(raw).decode("ascii")
        except OSError:
            return {"name": path.name, "type": "error", "content": "(Error reading file)"}
        return {
            "name": name,
            "type": "image",
            "mime": mime,
            "data_uri": f"data:{mime};base64,{b64}",
        }
    elif ext == ".pdf":
        try:
            raw = path.read_bytes()
            b64 = base64.b64encode(raw).decode("ascii")
        except OSError:
            return {"name": path.name, "type": "error", "content": "(Error reading file)"}
        return {
            "name": name,
            "type": "pdf",
            "data_uri": f"data:{mime};base64,{b64}",
        }
    elif ext == ".xlsx":
        try:
            raw = path.read_bytes()
            b64 = base64.b64encode(raw).decode("ascii")
        except OSError:
            return {"name": path.name, "type": "error", "content": "(Error reading file)"}
        return {
            "name": name,
            "type": "xlsx",
            "data_b64": b64,
        }
    else:
        # Binary / unknown — base64 download link
        try:
            raw = path.read_bytes()
            b64 = base64.b64encode(raw).decode("ascii")
        except OSError:
            return {"name": path.name, "type": "error", "content": "(Error reading file)"}
        return {
            "name": name,
            "type": "binary",
            "mime": mime,
            "data_uri": f"data:{mime};base64,{b64}",
        }


def load_previous_iteration(workspace: Path) -> dict[str, dict]:
    """Load previous iteration's feedback and outputs.

    Returns a map of run_id -> {"feedback": str, "outputs": list[dict]}.
    """
    result: dict[str, dict] = {}

    # Load feedback
    feedback_map: dict[str, str] = {}
    feedback_path = workspace / "feedback.json"
    if feedback_path.exists():
        try:
            data = read_json_utf8(feedback_path)
            feedback_map = {
                r["run_id"]: r["feedback"]
                for r in data.get("reviews", [])
                if r.get("feedback", "").strip()
            }
        except (json.JSONDecodeError, OSError, UnicodeDecodeError, KeyError):
            pass

    # Load runs (to get outputs)
    prev_runs = find_runs(workspace)
    for run in prev_runs:
        result[run["id"]] = {
            "feedback": feedback_map.get(run["id"], ""),
            "outputs": run.get("outputs", []),
        }

    # Also add feedback for run_ids that had feedback but no matching run
    for run_id, fb in feedback_map.items():
        if run_id not in result:
            result[run_id] = {"feedback": fb, "outputs": []}

    return result


def generate_html(
    runs: list[dict],
    skill_name: str,
    mode: str,
    previous: dict[str, dict] | None = None,
    benchmark: dict | None = None,
) -> str:
    """Generate the complete standalone HTML page with embedded data."""
    template_path = Path(__file__).parent / "viewer.html"
    template = read_text_utf8(template_path)

    # Build previous_feedback and previous_outputs maps for the template
    previous_feedback: dict[str, str] = {}
    previous_outputs: dict[str, list[dict]] = {}
    if previous:
        for run_id, data in previous.items():
            if data.get("feedback"):
                previous_feedback[run_id] = data["feedback"]
            if data.get("outputs"):
                previous_outputs[run_id] = data["outputs"]

    embedded = {
        "mode": mode,
        "skill_name": skill_name,
        "runs": runs,
        "previous_feedback": previous_feedback,
        "previous_outputs": previous_outputs,
    }
    if benchmark:
        embedded["benchmark"] = benchmark

    data_json = json_for_script_tag(embedded)

    return template.replace("/*__EMBEDDED_DATA__*/", f"const EMBEDDED_DATA = {data_json};")


def build_summary(
    *,
    mode: str,
    workspace: Path,
    skill_name: str,
    runs: list[dict],
    feedback_path: Path,
    previous_workspace: Path | None = None,
    benchmark_path: Path | None = None,
    static_path: Path | None = None,
    port: int | None = None,
    url: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "ok": True,
        "mode": mode,
        "workspace": str(workspace),
        "skill_name": skill_name,
        "run_count": len(runs),
        "feedback_path": str(feedback_path),
    }
    if previous_workspace:
        summary["previous_workspace"] = str(previous_workspace)
    if benchmark_path:
        summary["benchmark_path"] = str(benchmark_path)
    if static_path:
        summary["static_path"] = str(static_path)
    if port is not None:
        summary["port"] = port
    if url:
        summary["url"] = url
    if note:
        summary["note"] = note
    return summary


def emit_summary(summary: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(summary, ensure_ascii=False))
        return

    if summary["mode"] == "static":
        print("\n  Eval Viewer")
        print("  ─────────────────────────────────")
        print(f"  HTML:      {summary['static_path']}")
    else:
        print("\n  Eval Viewer")
        print("  ─────────────────────────────────")
        print(f"  URL:       {summary['url']}")

    print(f"  Workspace: {summary['workspace']}")
    print(f"  Feedback:  {summary['feedback_path']}")
    if "previous_workspace" in summary:
        print(f"  Previous:  {summary['previous_workspace']}")
    if "benchmark_path" in summary:
        print(f"  Benchmark: {summary['benchmark_path']}")
    if "note" in summary:
        print(f"  Note:      {summary['note']}")
    if summary["mode"] == "serve":
        print("\n  Press Ctrl+C to stop.\n")
    else:
        print("\n  Open the HTML file in a browser to review outputs.\n")


# ---------------------------------------------------------------------------
# HTTP server (stdlib only, zero dependencies)
# ---------------------------------------------------------------------------

class ReviewHandler(BaseHTTPRequestHandler):
    """Serves the review HTML and handles feedback saves.

    Regenerates the HTML on each page load so that refreshing the browser
    picks up new eval outputs without restarting the server.
    """

    def __init__(
        self,
        workspace: Path,
        skill_name: str,
        feedback_path: Path,
        previous: dict[str, dict],
        benchmark_path: Path | None,
        *args,
        **kwargs,
    ):
        self.workspace = workspace
        self.skill_name = skill_name
        self.feedback_path = feedback_path
        self.previous = previous
        self.benchmark_path = benchmark_path
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        if self.path == "/" or self.path == "/index.html":
            # Regenerate HTML on each request (re-scans workspace for new outputs)
            runs = find_runs(self.workspace)
            benchmark = None
            if self.benchmark_path and self.benchmark_path.exists():
                try:
                    benchmark = read_json_utf8(self.benchmark_path)
                except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                    pass
            html = generate_html(runs, self.skill_name, "serve", self.previous, benchmark)
            content = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == "/api/feedback":
            data = b"{}"
            if self.feedback_path.exists():
                data = self.feedback_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        if self.path == "/api/feedback":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                if not isinstance(data, dict) or "reviews" not in data:
                    raise ValueError("Expected JSON object with 'reviews' key")
                write_text_utf8(self.feedback_path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
                resp = b'{"ok":true}'
                self.send_response(200)
            except (json.JSONDecodeError, OSError, ValueError) as e:
                resp = json.dumps({"error": str(e)}).encode()
                self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
        else:
            self.send_error(404)

    def log_message(self, format: str, *args: object) -> None:
        # Suppress request logging to keep terminal clean
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and serve eval review")
    parser.add_argument("workspace", type=Path, help="Path to workspace directory")
    parser.add_argument("--port", "-p", type=int, default=3117, help="Server port (default: 3117)")
    parser.add_argument("--skill-name", "-n", type=str, default=None, help="Skill name for header")
    parser.add_argument(
        "--previous-workspace", type=Path, default=None,
        help="Path to previous iteration's workspace (shows old outputs and feedback as context)",
    )
    parser.add_argument(
        "--benchmark", type=Path, default=None,
        help="Path to benchmark.json to show in the Benchmark tab",
    )
    parser.add_argument(
        "--static", "-s", type=Path, default=None,
        help="Write standalone HTML to this path instead of starting a server",
    )
    parser.add_argument(
        "--json-summary",
        action="store_true",
        help="Print a machine-readable JSON summary instead of human-readable status text",
    )
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    if not workspace.is_dir():
        print(f"Error: {workspace} is not a directory", file=sys.stderr)
        sys.exit(1)

    runs = find_runs(workspace)
    if not runs:
        print(f"No runs found in {workspace}", file=sys.stderr)
        sys.exit(1)

    skill_name = args.skill_name or workspace.name.replace("-workspace", "")
    feedback_path = workspace / "feedback.json"

    previous: dict[str, dict] = {}
    if args.previous_workspace:
        previous = load_previous_iteration(args.previous_workspace.resolve())

    benchmark_path = args.benchmark.resolve() if args.benchmark else None
    benchmark = None
    if benchmark_path and benchmark_path.exists():
        try:
            benchmark = read_json_utf8(benchmark_path)
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            pass

    if args.static:
        static_path = args.static.resolve()
        html = generate_html(runs, skill_name, "static", previous, benchmark)
        static_path.parent.mkdir(parents=True, exist_ok=True)
        write_text_utf8(static_path, html)
        summary = build_summary(
            mode="static",
            workspace=workspace,
            skill_name=skill_name,
            runs=runs,
            feedback_path=feedback_path,
            previous_workspace=args.previous_workspace.resolve() if args.previous_workspace else None,
            benchmark_path=benchmark_path,
            static_path=static_path,
        )
        emit_summary(summary, json_only=args.json_summary)
        sys.exit(0)

    port = args.port
    handler = partial(ReviewHandler, workspace, skill_name, feedback_path, previous, benchmark_path)
    note = None
    try:
        server = HTTPServer(("127.0.0.1", port), handler)
    except OSError:
        # Fall back to an ephemeral port instead of trying to kill another process.
        server = HTTPServer(("127.0.0.1", 0), handler)
        port = server.server_address[1]
        note = f"Requested port {args.port} was unavailable, using {port} instead"

    url = f"http://localhost:{port}"
    summary = build_summary(
        mode="serve",
        workspace=workspace,
        skill_name=skill_name,
        runs=runs,
        feedback_path=feedback_path,
        previous_workspace=args.previous_workspace.resolve() if args.previous_workspace else None,
        benchmark_path=benchmark_path,
        port=port,
        url=url,
        note=note,
    )
    emit_summary(summary, json_only=args.json_summary)

    if not args.json_summary:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


if __name__ == "__main__":
    main()
