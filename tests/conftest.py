"""Pytest fixtures for MergeBlocker tests."""

import os
from unittest.mock import Mock

import pytest


@pytest.fixture(scope="session")
def check_env_vars():
    """Check if required environment variables are set."""
    try:
        api_key = os.getenv("LLM_API_KEY")
        if not api_key:
            pytest.skip("LLM_API_KEY not set - skipping LLM integration tests")
        return True
    except Exception:
        pytest.skip("Environment not configured - skipping integration tests")


@pytest.fixture
def mock_github_client():
    """Create a mock GitHub client for testing."""
    client = Mock()

    # Mock PR context
    client.get_pr_context.return_value = {
        "pr": {
            "number": 1,
            "title": "Test PR",
            "body": "Test description",
            "state": "open",
            "draft": False,
            "head_sha": "abc123",
            "base_branch": "main",
            "head_branch": "feature/test",
            "author": "test-user",
            "labels": [],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        },
        "files": [
            {
                "filename": "test.py",
                "status": "modified",
                "additions": 10,
                "deletions": 5,
                "changes": 15,
                "patch": "@@ -1,5 +1,10 @@\n+def test():\n+    pass",
            }
        ],
        "stats": {
            "total_files": 1,
            "total_additions": 10,
            "total_deletions": 5,
            "total_changes": 15,
        },
        "commits": [],
    }

    # Mock PR get
    client.get_pr.return_value = {
        "number": 1,
        "title": "Test PR",
        "body": "Test description",
        "state": "open",
        "draft": False,
        "head": {"sha": "abc123", "ref": "feature/test"},
        "base": {"ref": "main"},
        "user": {"login": "test-user"},
    }

    # Mock review creation
    client.create_review.return_value = True
    client.create_comment.return_value = True
    client.create_check_run.return_value = True

    return client


@pytest.fixture
def mock_code_analyzer():
    """Create a mock code analyzer for testing."""
    analyzer = Mock()

    # Mock PR analysis (JSON format)
    analyzer.analyze_pr.return_value = {
        "summary": "Test review summary",
        "critical_issues": ["Critical issue 1"],
        "suggestions": ["Suggestion 1", "Suggestion 2"],
        "inline_comments": [
            {
                "path": "test.py",
                "line": 5,
                "body": "Consider adding docstring",
            }
        ],
    }

    return analyzer


@pytest.fixture
def sample_pr_event():
    """Sample PR event payload."""
    return {
        "event_type": "pull_request",
        "action": "opened",
        "payload": {
            "pull_request": {
                "number": 1,
                "title": "Test PR",
                "body": "Test description",
                "state": "open",
                "draft": False,
                "head": {
                    "sha": "abc123",
                    "ref": "feature/test",
                },
                "base": {
                    "ref": "main",
                },
                "user": {
                    "login": "test-user",
                },
            },
            "repository": {
                "full_name": "owner/repo",
                "name": "repo",
                "owner": {
                    "login": "owner",
                },
            },
            "installation": {
                "id": 12345,
            },
        },
    }


@pytest.fixture
def sample_comment_event():
    """Sample comment event payload with command."""
    return {
        "event_type": "issue_comment",
        "action": "created",
        "payload": {
            "issue": {
                "number": 1,
                "title": "Test PR",
                "body": "Test description",
                "state": "open",
                "pull_request": {},  # Indicates this is a PR comment
            },
            "comment": {
                "id": 999,
                "body": "@MergeBlocker review",
                "user": {
                    "login": "reviewer-user",
                },
            },
            "repository": {
                "full_name": "owner/repo",
                "name": "repo",
                "owner": {
                    "login": "owner",
                },
            },
            "installation": {
                "id": 12345,
            },
        },
    }
