"""Webhook handler for GitHub events."""
import hmac
import hashlib
from typing import Dict, Any, Optional
from flask import Request
from config import Config


class WebhookHandler:
    """Handles GitHub webhook events."""
    
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
        signature = request.headers.get('X-Hub-Signature-256')
        if not signature:
            return False
        
        # Calculate expected signature
        mac = hmac.new(
            self.secret.encode(),
            msg=request.data,
            digestmod=hashlib.sha256
        )
        expected_signature = 'sha256=' + mac.hexdigest()
        
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
        event_type = request.headers.get('X-GitHub-Event')
        if not event_type:
            return None
        
        payload = request.get_json()
        if not payload:
            return None
        
        return {
            'event_type': event_type,
            'action': payload.get('action'),
            'payload': payload,
        }
    
    def should_process_pr_event(self, event: Dict[str, Any]) -> tuple[bool, str]:
        """
        Determine if we should process this PR event.
        
        Args:
            event: Parsed event dictionary
        
        Returns:
            Tuple of (should_process, reason)
        """
        if event['event_type'] != 'pull_request':
            return False, "Not a pull_request event"
        
        action = event['action']
        valid_actions = ['opened', 'reopened', 'synchronize', 'ready_for_review']
        
        if action not in valid_actions:
            return False, f"Action '{action}' not in {valid_actions}"
        
        pr = event['payload'].get('pull_request', {})
        
        # Skip draft PRs if configured
        if Config.SKIP_DRAFT_PRS and pr.get('draft', False):
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
        payload = event['payload']
        pr = payload['pull_request']
        repo = payload['repository']
        installation = payload['installation']
        
        return {
            'installation_id': installation['id'],
            'repo_full_name': repo['full_name'],
            'repo_name': repo['name'],
            'repo_owner': repo['owner']['login'],
            'pr_number': pr['number'],
            'pr_title': pr['title'],
            'pr_body': pr.get('body', ''),
            'pr_state': pr['state'],
            'pr_draft': pr.get('draft', False),
            'head_sha': pr['head']['sha'],
            'base_branch': pr['base']['ref'],
            'head_branch': pr['head']['ref'],
            'author': pr['user']['login'],
            'action': event['action'],
        }

