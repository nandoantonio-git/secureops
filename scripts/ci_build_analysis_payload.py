#!/usr/bin/env python3
"""Builds the POST /analyses JSON body for the GitHub Actions gate workflow.

Reads the diff between two commits, keeps only files SecureOps can actually
analyze (matching app/engine/parser.py's supported extensions -- duplicated
here deliberately rather than imported, since this script runs on the
Actions runner, outside the API container), and points each file's
content_ref at the same /workspace mount the api container is started with.
Prints nothing but the JSON payload to stdout so the workflow can pipe it
straight into curl; all progress/diagnostic output goes to stderr.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

_LANGUAGE_BY_EXTENSION = {
    ".py": "python",
    ".pyw": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
}


def _changed_paths(base_sha: str, head_sha: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", base_sha, head_sha],
        capture_output=True,
        check=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def _language_for(path: str) -> str | None:
    for extension, language in _LANGUAGE_BY_EXTENSION.items():
        if path.endswith(extension):
            return language
    return None


def build_payload(
    *,
    repository: str,
    pull_request_number: int,
    commit_sha: str,
    mode: str,
    base_sha: str,
    head_sha: str,
    workspace_mount: str,
) -> dict[str, object]:
    changed_files = []
    for path in _changed_paths(base_sha, head_sha):
        language = _language_for(path)
        if language is None:
            continue
        changed_files.append(
            {
                "path": path,
                "language": language,
                "content_ref": f"{workspace_mount.rstrip('/')}/{path}",
            },
        )

    return {
        "repository": repository,
        "pull_request_number": pull_request_number,
        "commit_sha": commit_sha,
        "trigger": "pull_request",
        "mode": mode,
        "changed_files": changed_files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, help="owner/name")
    parser.add_argument("--pull-request-number", required=True, type=int)
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--mode", default="blocking_enabled")
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--workspace-mount", default="/workspace")
    args = parser.parse_args()

    payload = build_payload(
        repository=args.repository,
        pull_request_number=args.pull_request_number,
        commit_sha=args.commit_sha,
        mode=args.mode,
        base_sha=args.base_sha,
        head_sha=args.head_sha,
        workspace_mount=args.workspace_mount,
    )

    print(
        f"{len(payload['changed_files'])} analyzable file(s) of "
        f"{len(_changed_paths(args.base_sha, args.head_sha))} changed",
        file=sys.stderr,
    )
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
