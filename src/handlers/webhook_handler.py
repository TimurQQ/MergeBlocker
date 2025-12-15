"""Webhook handler for GitHub events."""
import hashlib
import hmac
import re
from typing import Any, Dict, List, Optional

from flask import Request

from src.config import Config


class WebhookHandler:
    """Handles GitHub webhook events."""

    # Bot mention patterns for commands
    BOT_MENTION_PATTERNS = [
        r"@MergeBlocker\s+review",
        r"@mergeblocker\s+review",
    ]

    def __init__(self):
        self.secret = Config.GITHUB_WEBHOOK_SECRET

    def verify_signature(self, request: Request) -> bool:
        """
        Verify that the webhook request came from GitHub.

        Args:
            request: Flask request object

        Returns:
            True if signature is valid, False otherwise
        """
        signature = request.headers.get("X-Hub-Signature-256")
        if not signature:
            return False

        # Calculate expected signature
        mac = hmac.new(self.secret.encode(), msg=request.data, digestmod=hashlib.sha256)
        expected_signature = "sha256=" + mac.hexdigest()

        # Compare signatures
        return hmac.compare_digest(signature, expected_signature)

    def parse_event(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Parse webhook event from request.

        Args:
            request: Flask request object

        Returns:
            Dictionary with event details or None if invalid
        """
        event_type = request.headers.get("X-GitHub-Event")
        if not event_type:
            return None

        payload = request.get_json()
        if not payload:
            return None

        return {
            "event_type": event_type,
            "action": payload.get("action"),
            "payload": payload,
        }

    def should_process_pr_event(self, event: Dict[str, Any]) -> tuple[bool, str]:
        """
        Determine if we should process this PR event.

        Args:
            event: Parsed event dictionary

        Returns:
            Tuple of (should_process, reason)
        """
        if event["event_type"] != "pull_request":
            return False, "Not a pull_request event"

        action = event["action"]
        valid_actions = ["opened", "reopened", "synchronize", "ready_for_review"]

        if action not in valid_actions:
            return False, f"Action '{action}' not in {valid_actions}"

        pr = event["payload"].get("pull_request", {})

        # Skip draft PRs if configured
        if Config.SKIP_DRAFT_PRS and pr.get("draft", False):
            return False, "PR is in draft state"

        return True, "OK"

    def extract_pr_info(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant PR information from event.

        Args:
            event: Parsed event dictionary

        Returns:
            Dictionary with PR details
        """
        payload = event["payload"]
        pr = payload["pull_request"]
        repo = payload["repository"]
        
        # Check if installation exists in payload
        if "installation" not in payload:
            print(f"WARNING: No installation in webhook payload. Payload keys: {payload.keys()}")
            print(f"Full payload (first 500 chars): {str(payload)[:500]}")
            raise ValueError("No installation ID found in webhook payload. Is this a GitHub App webhook?")
        
        installation = payload["installation"]

        return {
            "installation_id": installation["id"],
            "repo_full_name": repo["full_name"],
            "repo_name": repo["name"],
            "repo_owner": repo["owner"]["login"],
            "pr_number": pr["number"],
            "pr_title": pr["title"],
            "pr_body": pr.get("body", ""),
            "pr_state": pr["state"],
            "pr_draft": pr.get("draft", False),
            "head_sha": pr["head"]["sha"],
            "base_branch": pr["base"]["ref"],
            "head_branch": pr["head"]["ref"],
            "author": pr["user"]["login"],
            "action": event["action"],
        }

    def is_comment_event(self, event: Dict[str, Any]) -> bool:
        """
        Check if event is a comment event.

        Args:
            event: Parsed event dictionary

        Returns:
            True if this is a comment event
        """
        return event["event_type"] == "issue_comment"

    def is_pr_comment(self, event: Dict[str, Any]) -> bool:
        """
        Check if comment is on a Pull Request (not an Issue).

        Args:
            event: Parsed event dictionary

        Returns:
            True if comment is on a PR
        """
        payload = event["payload"]
        issue = payload.get("issue", {})
        # PR comments have 'pull_request' key in issue object
        return "pull_request" in issue

    def extract_commands_from_comment(self, comment_body: str) -> List[str]:
        """
        Extract bot commands from comment text.

        Args:
            comment_body: Text of the comment

        Returns:
            List of commands found (e.g., ['review'])
        """
        commands = []
        for pattern in self.BOT_MENTION_PATTERNS:
            if re.search(pattern, comment_body, re.IGNORECASE):
                commands.append("review")
                break
        return commands

    def should_process_comment_command(self, event: Dict[str, Any]) -> tuple[bool, str, List[str]]:
        """
        Determine if we should process this comment as a command.

        Args:
            event: Parsed event dictionary

        Returns:
            Tuple of (should_process, reason, commands_list)
        """
        if not self.is_comment_event(event):
            return False, "Not a comment event", []

        action = event["action"]
        if action != "created":
            return False, f"Comment action '{action}' is not 'created'", []

        if not self.is_pr_comment(event):
            return False, "Comment is not on a Pull Request", []

        payload = event["payload"]
        comment = payload.get("comment", {})
        comment_body = comment.get("body", "")

        commands = self.extract_commands_from_comment(comment_body)
        if not commands:
            return False, "No bot commands found in comment", []

        return True, "OK", commands

    def extract_pr_info_from_comment(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract PR information from comment event.

        Args:
            event: Parsed event dictionary

        Returns:
            Dictionary with PR details
        """
        payload = event["payload"]
        issue = payload["issue"]  # In comment events, PR is represented as issue
        repo = payload["repository"]
        
        # Check if installation exists in payload
        if "installation" not in payload:
            print(f"WARNING: No installation in webhook payload. Payload keys: {payload.keys()}")
            print(f"Full payload (first 500 chars): {str(payload)[:500]}")
            raise ValueError("No installation ID found in webhook payload. Is this a GitHub App webhook?")
        
        installation = payload["installation"]
        comment = payload["comment"]

        return {
            "installation_id": installation["id"],
            "repo_full_name": repo["full_name"],
            "repo_name": repo["name"],
            "repo_owner": repo["owner"]["login"],
            "pr_number": issue["number"],
            "pr_title": issue["title"],
            "pr_body": issue.get("body", ""),
            "pr_state": issue["state"],
            "pr_draft": issue.get("draft", False),
            "comment_id": comment["id"],
            "comment_author": comment["user"]["login"],
            "action": "command_review",  # Custom action for command-triggered review
        }
