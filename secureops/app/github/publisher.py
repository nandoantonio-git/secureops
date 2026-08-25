"""Publishes generated PR feedback to a real GitHub Pull Request.

Everything upstream of this module (comments.py, status.py) only builds
payloads -- nothing before this point ever talks to the network. This is
the one place that does, and it is intentionally the thinnest possible
wrapper around PyGithub so the actual API calls stay mockable: callers
inject a ``github_client_factory`` instead of this module importing and
constructing ``Github(...)`` itself at call time.

Publishing is best-effort by design (mirrors the persistence pattern in
app/api/analyses.py): a missing token, a missing PR number, or a GitHub API
error all come back as a non-published ``PublishResult`` with a reason,
never an exception. A PR comment failing to post must not fail the
analysis response the caller already has.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from app.github.status import build_commit_status


class _PullRequestLike(Protocol):
    def create_issue_comment(self, body: str) -> Any: ...


class _CommitLike(Protocol):
    def create_status(
        self,
        *,
        state: str,
        target_url: str = "",
        description: str = "",
        context: str = "",
    ) -> Any: ...


class _RepositoryLike(Protocol):
    def get_pull(self, number: int) -> _PullRequestLike: ...

    def get_commit(self, sha: str) -> _CommitLike: ...


class _GithubClientLike(Protocol):
    def get_repo(self, full_name_or_id: str) -> _RepositoryLike: ...


GithubClientFactory = Callable[[str], _GithubClientLike]


@dataclass(frozen=True)
class PublishResult:
    """Outcome of a publish attempt -- never raises, always returns one of these."""

    published: bool
    reason: str | None = None


def _default_client_factory(token: str) -> _GithubClientLike:
    from github import Github

    return Github(token)


def publish_pr_feedback(
    *,
    repository: str,
    pull_request_number: int | None,
    commit_sha: str,
    comment_body: str,
    gate_decision: Mapping[str, Any],
    token: str | None,
    github_client_factory: GithubClientFactory | None = None,
) -> PublishResult:
    """Post the PR feedback comment and commit status to a real GitHub PR.

    Returns a ``PublishResult`` describing what happened instead of raising,
    so a caller can always keep serving the analysis response it already
    built regardless of whether publishing succeeded.
    """

    if not token:
        return PublishResult(published=False, reason="no_github_token")
    if not pull_request_number:
        return PublishResult(published=False, reason="no_pull_request_number")

    factory = github_client_factory or _default_client_factory

    try:
        client = factory(token)
        repo = client.get_repo(repository)
        repo.get_pull(pull_request_number).create_issue_comment(comment_body)

        status_payload = build_commit_status(gate_decision)
        repo.get_commit(commit_sha).create_status(
            state=status_payload["state"],
            description=status_payload["description"],
            context=status_payload["context"],
            target_url=status_payload.get("target_url", ""),
        )
    except Exception as exc:  # noqa: BLE001 - publishing must never break the caller
        return PublishResult(published=False, reason=f"github_error: {exc}")

    return PublishResult(published=True)


__all__ = ["GithubClientFactory", "PublishResult", "publish_pr_feedback"]
