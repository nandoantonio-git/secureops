"""Unit tests for the GitHub PR publishing path (app/github/publisher.py)."""

from app.github.publisher import publish_pr_feedback

_GATE_DECISION = {
    "analysis_id": "a-1",
    "mode": "advisory",
    "decision": "advisory_only",
    "reasons": ["Advisory mode does not block merge."],
    "blocking_findings": [],
}


class _FakeCommit:
    def __init__(self) -> None:
        self.status_calls: list[dict[str, object]] = []

    def create_status(self, **kwargs: object) -> None:
        self.status_calls.append(kwargs)


class _FakePullRequest:
    def __init__(self) -> None:
        self.comments: list[str] = []

    def create_issue_comment(self, body: str) -> None:
        self.comments.append(body)


class _FakeRepository:
    def __init__(self) -> None:
        self.pull = _FakePullRequest()
        self.commit = _FakeCommit()
        self.requested_pull_numbers: list[int] = []
        self.requested_commit_shas: list[str] = []

    def get_pull(self, number: int) -> _FakePullRequest:
        self.requested_pull_numbers.append(number)
        return self.pull

    def get_commit(self, sha: str) -> _FakeCommit:
        self.requested_commit_shas.append(sha)
        return self.commit


class _FakeGithubClient:
    def __init__(self, repo: _FakeRepository) -> None:
        self._repo = repo
        self.requested_repo_names: list[str] = []

    def get_repo(self, full_name: str) -> _FakeRepository:
        self.requested_repo_names.append(full_name)
        return self._repo


class _RaisingClient:
    def get_repo(self, full_name: str) -> "_RaisingClient":
        raise RuntimeError("boom")


def _publish(**overrides: object) -> object:
    kwargs = {
        "repository": "acme/widgets",
        "pull_request_number": 42,
        "commit_sha": "deadbeef",
        "comment_body": "## SecureOps PR feedback",
        "gate_decision": _GATE_DECISION,
        "token": "ghp_test_token",
    }
    kwargs.update(overrides)
    return publish_pr_feedback(**kwargs)


def test_skips_publishing_without_a_token() -> None:
    result = _publish(token=None)

    assert result.published is False
    assert result.reason == "no_github_token"


def test_skips_publishing_without_a_pull_request_number() -> None:
    result = _publish(pull_request_number=None)

    assert result.published is False
    assert result.reason == "no_pull_request_number"


def test_publishes_comment_and_commit_status_on_success() -> None:
    repo = _FakeRepository()
    client = _FakeGithubClient(repo)

    result = _publish(github_client_factory=lambda _token: client)

    assert result.published is True
    assert result.reason is None
    assert client.requested_repo_names == ["acme/widgets"]
    assert repo.requested_pull_numbers == [42]
    assert repo.pull.comments == ["## SecureOps PR feedback"]
    assert repo.requested_commit_shas == ["deadbeef"]
    assert repo.commit.status_calls == [
        {
            "state": "success",
            "description": "Advisory: findings were reported without blocking merge.",
            "context": "secureops/gate",
            "target_url": "",
        },
    ]


def test_a_github_api_error_never_raises() -> None:
    result = _publish(github_client_factory=lambda _token: _RaisingClient())

    assert result.published is False
    assert result.reason is not None
    assert result.reason.startswith("github_error:")
