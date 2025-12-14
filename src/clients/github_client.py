"""GitHub API client for interacting with Pull Requests."""
from typing import Any, Dict, List, Optional

from github import Github, GithubIntegration

from src.config import Config


class GitHubClient:
    """Client for GitHub API operations."""

    def __init__(self):
        self.app_id = Config.GITHUB_APP_ID
        self.private_key = Config.get_private_key()
        self._installation_clients: Dict[int, Github] = {}

    def get_installation_client(self, installation_id: int) -> Github:
        """Get or create a GitHub client for a specific installation."""
        if installation_id not in self._installation_clients:
            integration = GithubIntegration(self.app_id, self.private_key)
            access_token = integration.get_access_token(installation_id).token
            self._installation_clients[installation_id] = Github(access_token)

        return self._installation_clients[installation_id]

    def get_pr_context(self, installation_id: int, repo_full_name: str, pr_number: int) -> Dict[str, Any]:
        """
        Get full context of a Pull Request.

        Returns:
            Dictionary containing PR details, files, and diffs
        """
        client = self.get_installation_client(installation_id)
        repo = client.get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)

        # Get changed files
        files = []
        total_additions = 0
        total_deletions = 0

        for file in pr.get_files():
            files.append(
                {
                    "filename": file.filename,
                    "status": file.status,  # added, modified, removed
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "patch": file.patch if hasattr(file, "patch") else None,
                }
            )
            total_additions += file.additions
            total_deletions += file.deletions

        # Get commits (last 5 for context)
        commits = []
        for commit in list(pr.get_commits())[-5:]:
            commits.append(
                {
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "author": commit.commit.author.name,
                }
            )

        # Get labels
        labels = [label.name for label in pr.labels]

        return {
            "pr": {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body or "",
                "state": pr.state,
                "draft": pr.draft,
                "head_sha": pr.head.sha,
                "base_branch": pr.base.ref,
                "head_branch": pr.head.ref,
                "author": pr.user.login,
                "labels": labels,
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
            },
            "files": files,
            "stats": {
                "total_files": len(files),
                "total_additions": total_additions,
                "total_deletions": total_deletions,
                "total_changes": total_additions + total_deletions,
            },
            "commits": commits,
        }

    def get_pr(self, installation_id: int, repo_full_name: str, pr_number: int) -> Dict[str, Any]:
        """
        Get basic Pull Request information.

        Args:
            installation_id: GitHub App installation ID
            repo_full_name: Repository full name (owner/repo)
            pr_number: Pull Request number

        Returns:
            Dictionary containing basic PR details
        """
        client = self.get_installation_client(installation_id)
        repo = client.get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)

        return {
            "number": pr.number,
            "title": pr.title,
            "body": pr.body or "",
            "state": pr.state,
            "draft": pr.draft,
            "head": {
                "sha": pr.head.sha,
                "ref": pr.head.ref,
            },
            "base": {
                "ref": pr.base.ref,
            },
            "user": {
                "login": pr.user.login,
            },
        }

    def create_review(
        self,
        installation_id: int,
        repo_full_name: str,
        pr_number: int,
        head_sha: str,
        body: str,
        comments: Optional[List[Dict[str, Any]]] = None,
        event: str = "COMMENT",
    ) -> bool:
        """
        Create a review on a Pull Request.

        Args:
            installation_id: GitHub installation ID
            repo_full_name: Full repository name (owner/repo)
            pr_number: Pull request number
            head_sha: SHA of the head commit
            body: Review body/summary
            comments: List of inline comments with format:
                      [{'path': str, 'line': int, 'body': str}, ...]
            event: Review event type (COMMENT, APPROVE, REQUEST_CHANGES)

        Returns:
            True if successful, False otherwise
        """
        try:
            client = self.get_installation_client(installation_id)
            repo = client.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)

            # Prepare review comments
            review_comments = []
            if comments:
                for comment in comments:
                    review_comments.append(
                        {
                            "path": comment["path"],
                            "line": comment["line"],
                            "body": comment["body"],
                        }
                    )

            # Create review
            if review_comments:
                pr.create_review(
                    body=body,
                    event=event,
                    comments=review_comments,
                )
            else:
                # Just a comment without inline reviews
                pr.create_review(
                    body=body,
                    event=event,
                )

            return True

        except Exception as e:
            print(f"Error creating review: {e}")
            return False

    def create_comment(self, installation_id: int, repo_full_name: str, pr_number: int, body: str) -> bool:
        """
        Create a simple comment on a Pull Request.

        Args:
            installation_id: GitHub installation ID
            repo_full_name: Full repository name (owner/repo)
            pr_number: Pull request number
            body: Comment body

        Returns:
            True if successful, False otherwise
        """
        try:
            client = self.get_installation_client(installation_id)
            repo = client.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)
            pr.create_issue_comment(body)
            return True

        except Exception as e:
            print(f"Error creating comment: {e}")
            return False

    def create_check_run(
        self,
        installation_id: int,
        repo_full_name: str,
        head_sha: str,
        name: str = "AI Code Review",
        status: str = "in_progress",
        conclusion: Optional[str] = None,
        title: Optional[str] = None,
        summary: Optional[str] = None,
    ) -> bool:
        """
        Create or update a check run (for visual status).

        Args:
            installation_id: GitHub installation ID
            repo_full_name: Full repository name
            head_sha: Commit SHA
            name: Check run name
            status: in_progress, queued, completed
            conclusion: success, failure, neutral, cancelled, skipped (when status=completed)
            title: Check run title
            summary: Check run summary

        Returns:
            True if successful, False otherwise
        """
        try:
            client = self.get_installation_client(installation_id)
            repo = client.get_repo(repo_full_name)

            output = None
            if title or summary:
                output = {
                    "title": title or "AI Code Review",
                    "summary": summary or "Review completed",
                }

            repo.create_check_run(
                name=name,
                head_sha=head_sha,
                status=status,
                conclusion=conclusion,
                output=output,
            )
            return True

        except Exception as e:
            print(f"Error creating check run: {e}")
            return False
