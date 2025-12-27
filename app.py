"""Main Quart application for MergeBlocker GitHub App."""

import asyncio
import logging

from github import GithubException
from quart import Quart, jsonify, request

from src.analysis.code_analyzer import CodeAnalyzer
from src.analysis.review_formatter import ReviewFormatter
from src.clients.github_client import GitHubClient
from src.config import Config
from src.handlers.webhook_handler import WebhookHandler

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize Quart app
app = Quart(__name__)

# Initialize components
webhook_handler = WebhookHandler()
github_client = GitHubClient()
code_analyzer = CodeAnalyzer()
review_formatter = ReviewFormatter()


@app.route("/", methods=["GET"])
async def home():
    """Health check endpoint."""
    return jsonify({"status": "ok", "app": "MergeBlocker", "version": "1.0.0"})


async def handle_review_command(pr_info: dict):
    """Handle @MergeBlocker review command."""
    logger.info(
        f"Extracted PR info - installation_id: {pr_info.get('installation_id')}, "
        f"repo: {pr_info.get('repo_full_name')}, PR: {pr_info.get('pr_number')}"
    )

    try:
        pr_details = await asyncio.to_thread(
            github_client.get_pr,
            installation_id=pr_info["installation_id"],
            repo_full_name=pr_info["repo_full_name"],
            pr_number=pr_info["pr_number"],
        )

        pr_info.update(
            {
                "head_sha": pr_details["head"]["sha"],
                "base_branch": pr_details["base"]["ref"],
                "head_branch": pr_details["head"]["ref"],
                "author": pr_details["user"]["login"],
            }
        )

        logger.info(
            f"Processing command-triggered review for PR #{pr_info['pr_number']} "
            f"in {pr_info['repo_full_name']} (SHA: {pr_info['head_sha'][:7]})"
        )

        # Run review in background to avoid blocking webhook response
        asyncio.create_task(process_pr_review(pr_info))
        return jsonify({"message": "Review started by command"}), 200

    except GithubException as e:
        if e.status == 401:
            error_msg = (
                f"GitHub App not installed in {pr_info['repo_full_name']} "
                f"(installation_id: {pr_info['installation_id']}). "
                f"Install at: https://github.com/apps/{Config.GITHUB_APP_NAME}"
            )
            logger.error(error_msg)
            return jsonify({"error": "GitHub App not installed in repository"}), 403
        else:
            logger.error(f"GitHub API error: {e}", exc_info=True)
            return jsonify({"error": f"GitHub API error: {e.status}"}), 500

    except Exception as e:
        logger.error(f"Error processing command review: {e}", exc_info=True)
        return jsonify({"error": "Failed to process command"}), 500


async def handle_comment_reply(event: dict):
    """Handle reply to bot's comment - continue conversation."""
    logger.info("Processing reply to bot's comment")

    try:
        payload = event["payload"]
        comment = payload["comment"]
        repo = payload["repository"]
        installation = payload["installation"]

        # Get PR number - different structure for different event types
        if event["event_type"] == "pull_request_review_comment":
            pr_number = payload["pull_request"]["number"]
        else:  # issue_comment
            pr_number = payload["issue"]["number"]

        reply_to_id = comment.get("in_reply_to_id")
        user_question = comment["body"]

        logger.info(f"Reply to comment {reply_to_id} in PR #{pr_number}: {user_question[:100]}")

        # Get parent comment to understand context
        parent_comment = await asyncio.to_thread(
            github_client.get_review_comment, installation["id"], repo["full_name"], reply_to_id
        )

        if not parent_comment:
            logger.error(f"Could not find parent comment {reply_to_id}")
            return jsonify({"error": "Parent comment not found"}), 404

        # Only respond if parent comment is from bot
        if parent_comment["user"] not in ["MergeBlocker[bot]", "mergeblocker[bot]"]:
            logger.info(f"Parent comment is from {parent_comment['user']}, not bot. Skipping.")
            return jsonify({"message": "Not a reply to bot"}), 200

        # Get PR context
        pr_context = await asyncio.to_thread(github_client.get_pr_context, installation["id"], repo["full_name"], pr_number)

        # Build prompt with conversation history
        conversation_prompt = f"""User asked a follow-up question about this code review comment:

**Original Bot Comment (at {parent_comment['path']}:{parent_comment['line']})**:
{parent_comment['body']}

**User's Question**:
{user_question}

**Code Context** (file: {parent_comment['path']}):
```
{_get_code_snippet_for_line(pr_context, parent_comment['path'], parent_comment['line'])}
```

Please provide a helpful, specific answer to the user's question. Be concise and refer to the code when relevant.
"""

        # Generate response via LLM
        system_prompt = (
            "You are a helpful code review assistant. "
            "Answer user's questions about code review comments concisely and accurately."
        )
        reply_text = await code_analyzer.client.generate(user_prompt=conversation_prompt, system_prompt=system_prompt)

        # Post reply
        success = await asyncio.to_thread(
            github_client.create_review_comment_reply,
            installation["id"],
            repo["full_name"],
            pr_number,
            reply_to_id,
            f"🤖 {reply_text}",
        )

        if success:
            logger.info(f"Posted reply to comment {reply_to_id} in PR #{pr_number}")
            return jsonify({"message": "Reply posted"}), 200
        else:
            logger.error("Failed to post reply")
            return jsonify({"error": "Failed to post reply"}), 500

    except Exception as e:
        logger.error(f"Error handling comment reply: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


def _get_code_snippet_for_line(pr_context: dict, file_path: str, line: int, context_lines: int = 5) -> str:
    """Get code snippet around specific line."""
    for file in pr_context["files"]:
        if file["filename"] == file_path and file["patch"]:
            # Extract relevant lines from patch
            patch_lines = file["patch"].split("\n")
            # Simple heuristic: return patch around the line
            return "\n".join(patch_lines[: min(len(patch_lines), context_lines * 2)])
    return "(code not available)"


async def handle_pr_opened(pr_info: dict):
    """Handle PR opened event - post welcome comment."""
    logger.info(f"New PR opened: #{pr_info['pr_number']} in {pr_info['repo_full_name']}")

    try:
        welcome_message = (
            "👋 Hi! I'm MergeBlocker, your AI code review assistant.\n\n"
            "To start an AI-powered code review, simply comment:\n"
            "```\n"
            "@MergeBlocker review\n"
            "```\n\n"
            "I'll analyze your changes and provide detailed feedback!"
        )

        await asyncio.to_thread(
            github_client.create_comment,
            installation_id=pr_info["installation_id"],
            repo_full_name=pr_info["repo_full_name"],
            pr_number=pr_info["pr_number"],
            body=welcome_message,
        )

        logger.info(f"Posted welcome comment to PR #{pr_info['pr_number']}")
        return jsonify({"message": "Welcome comment posted"}), 200

    except Exception as e:
        logger.error(f"Error posting welcome comment: {e}", exc_info=True)
        return jsonify({"error": "Failed to post welcome comment"}), 500


@app.route("/webhook", methods=["POST"])
async def webhook():
    """Handle GitHub webhook events."""

    # Verify signature
    if not await webhook_handler.verify_signature(request):
        logger.warning("Invalid webhook signature")
        return jsonify({"error": "Invalid signature"}), 401

    # Parse event
    event = await webhook_handler.parse_event(request)
    if not event:
        logger.warning("Failed to parse event")
        return jsonify({"error": "Invalid event"}), 400

    logger.info(f"Received {event['event_type']} event with action: {event.get('action')}")

    # Handle comment commands (e.g., @MergeBlocker review)
    if webhook_handler.is_comment_event(event):
        # Check if this is a reply to bot's comment (conversation)
        if webhook_handler.is_reply_to_comment(event):
            logger.info("Detected reply to comment")
            return await handle_comment_reply(event)

        should_process, reason, commands = webhook_handler.should_process_comment_command(event)
        if should_process and "review" in commands:
            logger.info("Processing review command from comment")
            pr_info = webhook_handler.extract_pr_info_from_comment(event)
            return await handle_review_command(pr_info)
        else:
            logger.info(f"Skipping comment event: {reason}")
            return jsonify({"message": f"Skipped: {reason}"}), 200

    # Handle PR opened event - post welcome comment
    if event.get("event_type") == "pull_request" and event.get("action") == "opened":
        pr_info = webhook_handler.extract_pr_info(event)
        return await handle_pr_opened(pr_info)

    # For other events, just acknowledge
    logger.info(f"Skipping event: {event.get('event_type')} - {event.get('action')}")
    return jsonify({"message": "Event acknowledged, use @MergeBlocker review to start analysis"}), 200


async def process_pr_review(pr_info: dict):
    """
    Process PR review - fetch context, analyze, and post review.

    Args:
        pr_info: PR information from webhook
    """
    installation_id = pr_info["installation_id"]
    repo_full_name = pr_info["repo_full_name"]
    pr_number = pr_info["pr_number"]
    head_sha = pr_info["head_sha"]

    try:
        # Step 1: Create initial check run (optional - for status visibility)
        logger.info(f"Creating initial check run for PR #{pr_number}")
        await asyncio.to_thread(
            github_client.create_check_run,
            installation_id=installation_id,
            repo_full_name=repo_full_name,
            head_sha=head_sha,
            name="AI Code Review",
            status="in_progress",
            title="Analyzing code changes...",
            summary="AI code review is in progress. This may take a minute.",
        )

        # Step 2: Get PR context
        logger.info(f"Fetching PR context for #{pr_number}")
        pr_context = await asyncio.to_thread(
            github_client.get_pr_context,
            installation_id=installation_id,
            repo_full_name=repo_full_name,
            pr_number=pr_number,
        )

        # Step 2.5: Try to read AGENTS.md from repository
        logger.info(f"Attempting to read AGENTS.md for PR #{pr_number}")
        agents_md_content = await asyncio.to_thread(
            github_client.get_file_content,
            installation_id=installation_id,
            repo_full_name=repo_full_name,
            file_path="AGENTS.md",
            ref=pr_info.get("base_branch", None),
        )
        if agents_md_content:
            logger.info(f"Successfully loaded AGENTS.md ({len(agents_md_content)} chars)")
        else:
            logger.info("AGENTS.md not found in repository")

        # Step 3: AI analysis (true async, no thread pool)
        logger.info(f"Running AI analysis for PR #{pr_number}")
        review_result = await code_analyzer.analyze_pr(pr_context, agents_md_content=agents_md_content)

        # Step 4: Format review
        logger.info(f"Formatting review for PR #{pr_number}")
        review_body = review_formatter.format_review_comment(
            review_result=review_result,
            pr_info=pr_info,
        )

        # Step 5: Post review
        inline_comments = review_result.get("inline_comments", [])

        # Format inline comments
        formatted_comments = []
        for comment in inline_comments:
            formatted_comments.append(
                {
                    "path": comment["path"],
                    "line": comment["line"],
                    "body": review_formatter.format_inline_comment(comment),
                }
            )

        logger.info(f"Posting review for PR #{pr_number} " f"({len(formatted_comments)} inline comments)")

        success = await asyncio.to_thread(
            github_client.create_review,
            installation_id=installation_id,
            repo_full_name=repo_full_name,
            pr_number=pr_number,
            head_sha=head_sha,
            body=review_body,
            comments=formatted_comments if formatted_comments else None,
            event="COMMENT",
        )

        if not success:
            logger.error(f"Failed to post review for PR #{pr_number}")
            # Try posting a simple comment as fallback
            await asyncio.to_thread(
                github_client.create_comment,
                installation_id=installation_id,
                repo_full_name=repo_full_name,
                pr_number=pr_number,
                body=review_body,
            )

        # Step 6: Update check run to completed
        check_summary = review_formatter.format_check_run_summary(
            review_result=review_result,
            pr_info=pr_info,
        )

        await asyncio.to_thread(
            github_client.create_check_run,
            installation_id=installation_id,
            repo_full_name=repo_full_name,
            head_sha=head_sha,
            name="AI Code Review",
            status="completed",
            conclusion="success",
            title=check_summary["title"],
            summary=check_summary["summary"],
        )

        logger.info(f"Successfully completed review for PR #{pr_number}")

    except Exception as e:
        logger.error(f"Error in process_pr_review for PR #{pr_number}: {e}", exc_info=True)

        # Post error comment
        try:
            error_comment = review_formatter.format_error_comment(
                error_message=str(e),
                pr_info=pr_info,
            )
            await asyncio.to_thread(
                github_client.create_comment,
                installation_id=installation_id,
                repo_full_name=repo_full_name,
                pr_number=pr_number,
                body=error_comment,
            )

            # Update check run to failed
            await asyncio.to_thread(
                github_client.create_check_run,
                installation_id=installation_id,
                repo_full_name=repo_full_name,
                head_sha=head_sha,
                name="AI Code Review",
                status="completed",
                conclusion="failure",
                title="❌ Review Failed",
                summary=f"An error occurred during code review: {str(e)}",
            )
        except Exception as inner_e:
            logger.error(f"Failed to post error comment: {inner_e}", exc_info=True)


if __name__ == "__main__":
    # Validate configuration
    try:
        Config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        exit(1)

    # Start Flask server
    logger.info(f"Starting MergeBlocker on {Config.HOST}:{Config.PORT}")
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
    )
