"""Tests for webhook handler."""

import pytest

from src.handlers.webhook_handler import WebhookHandler


class TestWebhookHandler:
    """Tests for WebhookHandler class."""

    @pytest.fixture
    def handler(self):
        """Create a WebhookHandler instance."""
        return WebhookHandler()

    def test_should_process_pr_event_opened(self, handler, sample_pr_event):
        """Test processing opened PR event."""
        should_process, reason = handler.should_process_pr_event(sample_pr_event)
        assert should_process is True
        assert reason == "OK"

    def test_should_process_pr_event_synchronized(self, handler, sample_pr_event):
        """Test processing synchronized PR event."""
        sample_pr_event["action"] = "synchronize"
        should_process, reason = handler.should_process_pr_event(sample_pr_event)
        assert should_process is True
        assert reason == "OK"

    def test_should_not_process_closed_pr(self, handler, sample_pr_event):
        """Test skipping closed PR event."""
        sample_pr_event["action"] = "closed"
        should_process, reason = handler.should_process_pr_event(sample_pr_event)
        assert should_process is False
        assert "Action 'closed' not in" in reason

    def test_should_not_process_draft_pr(self, handler, sample_pr_event):
        """Test skipping draft PR."""
        sample_pr_event["payload"]["pull_request"]["draft"] = True
        should_process, reason = handler.should_process_pr_event(sample_pr_event)
        assert should_process is False
        assert reason == "PR is in draft state"

    def test_extract_pr_info(self, handler, sample_pr_event):
        """Test extracting PR information."""
        pr_info = handler.extract_pr_info(sample_pr_event)

        assert pr_info["installation_id"] == 12345
        assert pr_info["repo_full_name"] == "owner/repo"
        assert pr_info["pr_number"] == 1
        assert pr_info["pr_title"] == "Test PR"
        assert pr_info["head_sha"] == "abc123"
        assert pr_info["author"] == "test-user"

    def test_is_comment_event(self, handler, sample_comment_event):
        """Test identifying comment events."""
        assert handler.is_comment_event(sample_comment_event) is True

    def test_is_not_comment_event(self, handler, sample_pr_event):
        """Test identifying non-comment events."""
        assert handler.is_comment_event(sample_pr_event) is False

    def test_is_pr_comment(self, handler, sample_comment_event):
        """Test identifying PR comments."""
        assert handler.is_pr_comment(sample_comment_event) is True

    def test_is_not_pr_comment(self, handler, sample_comment_event):
        """Test identifying non-PR comments (issue comments)."""
        # Remove pull_request key to make it an issue comment
        del sample_comment_event["payload"]["issue"]["pull_request"]
        assert handler.is_pr_comment(sample_comment_event) is False

    def test_extract_commands_from_comment(self, handler):
        """Test extracting commands from comment text."""
        # Test with @MergeBlocker review
        commands = handler.extract_commands_from_comment("@MergeBlocker review")
        assert "review" in commands

        # Test with lowercase
        commands = handler.extract_commands_from_comment("@mergeblocker review")
        assert "review" in commands

        # Test without command
        commands = handler.extract_commands_from_comment("This is a regular comment")
        assert len(commands) == 0

    def test_should_process_comment_command(self, handler, sample_comment_event):
        """Test processing comment command."""
        should_process, reason, commands = handler.should_process_comment_command(sample_comment_event)

        assert should_process is True
        assert reason == "OK"
        assert "review" in commands

    def test_should_not_process_non_created_comment(self, handler, sample_comment_event):
        """Test not processing edited comment."""
        sample_comment_event["action"] = "edited"
        should_process, reason, commands = handler.should_process_comment_command(sample_comment_event)

        assert should_process is False
        assert "Comment action 'edited' is not 'created'" in reason

    def test_extract_pr_info_from_comment(self, handler, sample_comment_event):
        """Test extracting PR info from comment event."""
        pr_info = handler.extract_pr_info_from_comment(sample_comment_event)

        assert pr_info["installation_id"] == 12345
        assert pr_info["repo_full_name"] == "owner/repo"
        assert pr_info["pr_number"] == 1
        assert pr_info["comment_id"] == 999
        assert pr_info["comment_author"] == "reviewer-user"
        assert pr_info["action"] == "command_review"
