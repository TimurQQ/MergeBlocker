"""GitHub API client for interacting with Pull Requests."""

import traceback
from typing import Any, Dict, List, Optional

from github import Auth, Github, GithubIntegration

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
            try:
                print(f"Creating client for installation_id: {installation_id}")
                print(f"Using GitHub App ID: {self.app_id}")
                print(f"Private key length: {len(self.private_key)} chars")

                auth = Auth.AppAuth(self.app_id, self.private_key)
                integration = GithubIntegration(auth=auth)

                # Try to list installations for debugging
                try:
                    installations = integration.get_installations()
                    available_ids = [inst.id for inst in installations]
                    print(f"Available installation IDs: {available_ids}")

                    if installation_id not in available_ids:
                        print(f"WARNING: installation_id {installation_id} not in available installations!")
                        print("This means the GitHub App is not installed in this repository.")
                except Exception as list_error:
                    print(f"Could not list installations: {list_error}")

                access_token = integration.get_access_token(installation_id).token
                print(f"Successfully obtained access token for installation {installation_id}")
                self._installation_clients[installation_id] = Github(access_token)
            except Exception as e:
                print(f"Error creating installation client: {e}")
                print(f"App ID: {self.app_id}")
                print(f"Installation ID: {installation_id}")
                raise

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

    def get_file_content(
        self, installation_id: int, repo_full_name: str, file_path: str, ref: Optional[str] = None
    ) -> Optional[str]:
        """
        Get content of a file from repository.

        Args:
            installation_id: GitHub App installation ID
            repo_full_name: Repository full name (owner/repo)
            file_path: Path to file in repository
            ref: Branch/commit ref (default: default branch)

        Returns:
            File content as string, or None if file doesn't exist
        """
        try:
            client = self.get_installation_client(installation_id)
            repo = client.get_repo(repo_full_name)
            file_content = repo.get_contents(file_path, ref=ref)
            if isinstance(file_content, list):
                return None
            return file_content.decoded_content.decode("utf-8")
        except Exception as e:
            print(f"File {file_path} not found or error: {e}")
            return None

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

    def get_review_comment(
        self, installation_id: int, repo_full_name: str, pr_number: int, comment_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific review comment by ID.

        According to PyGithub docs, PullRequestComment has these attributes:
        - body, commit_id, created_at, diff_hunk, id, in_reply_to_id
        - original_commit_id, original_position, path, position
        - pull_request_url, updated_at, url, html_url, user

        Args:
            installation_id: GitHub installation ID
            repo_full_name: Full repository name
            pr_number: Pull request number (not used, but kept for compatibility)
            comment_id: Comment ID

        Returns:
            Dictionary with comment details or None if not found
        """
        try:
            print(f"Getting review comment {comment_id} from PR #{pr_number} in {repo_full_name}")
            client = self.get_installation_client(installation_id)
            repo = client.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)
            print(f"Got PR #{pr_number}, fetching comment {comment_id}...")
            comment = pr.get_review_comment(comment_id)
            print(f"Successfully retrieved comment {comment_id}")

            return {
                "id": comment.id,
                "body": comment.body,
                "path": comment.path,
                "position": comment.position,  # Position in diff, not line number
                "original_position": comment.original_position,
                "diff_hunk": comment.diff_hunk,
                "user": comment.user.login,
                "created_at": comment.created_at.isoformat(),
                "in_reply_to_id": comment.in_reply_to_id,
                "commit_id": comment.commit_id,
            }
        except Exception as e:
            print(f"Error getting review comment {comment_id} in PR #{pr_number}: {e}")
            traceback.print_exc()
            return None

    def create_review_comment_reply(
        self, installation_id: int, repo_full_name: str, pr_number: int, comment_id: int, body: str
    ) -> bool:
        """
        Create a reply to a review comment.

        Args:
            installation_id: GitHub installation ID
            repo_full_name: Full repository name
            pr_number: Pull request number
            comment_id: ID of comment to reply to
            body: Reply text

        Returns:
            True if successful
        """
        try:
            print(f"Creating reply to comment {comment_id} in PR #{pr_number}")
            client = self.get_installation_client(installation_id)
            repo = client.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)

            # Create reply to review comment
            print(f"Posting reply (body length: {len(body)} chars)...")
            pr.create_review_comment_reply(comment_id, body)
            print(f"Successfully posted reply to comment {comment_id}")
            return True

        except Exception as e:
            print(f"Error creating review comment reply: {e}")
            traceback.print_exc()
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

    def create_reaction(
        self, installation_id: int, repo_full_name: str, comment_id: int, reaction: str, pr_number: int = None
    ) -> bool:
        """
        Create reaction on a comment.

        Args:
            installation_id: GitHub App installation ID
            repo_full_name: Repository (owner/repo)
            comment_id: Comment ID
            reaction: One of: +1, -1, laugh, confused, heart, hooray, rocket, eyes
            pr_number: PR/Issue number (required for comments)

        Returns:
            True if successful
        """
        try:
            client = self.get_installation_client(installation_id)
            repo = client.get_repo(repo_full_name)

            if not pr_number:
                print("❌ PR number required for create_reaction")
                return False

            # Try to get comment - first as review comment, then as issue comment
            try:
                # Review comment (on code lines in Files Changed tab)
                pr = repo.get_pull(pr_number)
                comment = pr.get_review_comment(comment_id)
                print(f"✅ Found review comment {comment_id}")
            except Exception:
                # Issue comment (in Conversation tab)
                issue = repo.get_issue(pr_number)  # PR is also an issue in GitHub API
                comment = issue.get_comment(comment_id)
                print(f"✅ Found issue comment {comment_id}")

            # Create reaction
            comment.create_reaction(reaction)

            print(f"✅ Created {reaction} reaction on comment {comment_id}")
            return True

        except Exception as e:
            print(f"❌ Error creating reaction: {e}")
            traceback.print_exc()
            return False
