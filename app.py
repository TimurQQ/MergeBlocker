"""Main Flask application for MergeBlocker GitHub App."""
import logging
from flask import Flask, request, jsonify
from config import Config
from webhook_handler import WebhookHandler
from github_client import GitHubClient
from code_analyzer import CodeAnalyzer
from review_formatter import ReviewFormatter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize components
webhook_handler = WebhookHandler()
github_client = GitHubClient()
code_analyzer = CodeAnalyzer()
review_formatter = ReviewFormatter()


@app.route('/', methods=['GET'])
def home():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'app': 'MergeBlocker',
        'version': '1.0.0'
    })


@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle GitHub webhook events."""
    
    # Verify signature
    if not webhook_handler.verify_signature(request):
        logger.warning("Invalid webhook signature")
        return jsonify({'error': 'Invalid signature'}), 401
    
    # Parse event
    event = webhook_handler.parse_event(request)
    if not event:
        logger.warning("Failed to parse event")
        return jsonify({'error': 'Invalid event'}), 400
    
    logger.info(f"Received {event['event_type']} event with action: {event.get('action')}")
    
    # Check if we should process this event
    should_process, reason = webhook_handler.should_process_pr_event(event)
    if not should_process:
        logger.info(f"Skipping event: {reason}")
        return jsonify({'message': f'Skipped: {reason}'}), 200
    
    # Extract PR info
    pr_info = webhook_handler.extract_pr_info(event)
    logger.info(
        f"Processing PR #{pr_info['pr_number']} in {pr_info['repo_full_name']} "
        f"(SHA: {pr_info['head_sha'][:7]})"
    )
    
    # Process PR review asynchronously (in production, use a task queue)
    try:
        process_pr_review(pr_info)
        return jsonify({'message': 'Review started'}), 200
    except Exception as e:
        logger.error(f"Error processing PR review: {e}", exc_info=True)
        return jsonify({'error': 'Internal error'}), 500


def process_pr_review(pr_info: dict):
    """
    Process PR review - fetch context, analyze, and post review.
    
    Args:
        pr_info: PR information from webhook
    """
    installation_id = pr_info['installation_id']
    repo_full_name = pr_info['repo_full_name']
    pr_number = pr_info['pr_number']
    head_sha = pr_info['head_sha']
    
    try:
        # Step 1: Create initial check run (optional - for status visibility)
        logger.info(f"Creating initial check run for PR #{pr_number}")
        github_client.create_check_run(
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
        pr_context = github_client.get_pr_context(
            installation_id=installation_id,
            repo_full_name=repo_full_name,
            pr_number=pr_number,
        )
        
        # Step 3: Quick deterministic checks
        logger.info(f"Running quick checks for PR #{pr_number}")
        quick_warnings = code_analyzer.quick_check(pr_context['files'])
        
        # Step 4: AI analysis
        logger.info(f"Running AI analysis for PR #{pr_number}")
        review_result = code_analyzer.analyze_pr(pr_context)
        
        # Step 5: Format review
        logger.info(f"Formatting review for PR #{pr_number}")
        review_body = review_formatter.format_review_comment(
            review_result=review_result,
            pr_info=pr_info,
            quick_warnings=quick_warnings,
        )
        
        # Step 6: Post review
        inline_comments = review_result.get('inline_comments', [])
        
        # Format inline comments
        formatted_comments = []
        for comment in inline_comments:
            formatted_comments.append({
                'path': comment['path'],
                'line': comment['line'],
                'body': review_formatter.format_inline_comment(comment),
            })
        
        logger.info(
            f"Posting review for PR #{pr_number} "
            f"({len(formatted_comments)} inline comments)"
        )
        
        success = github_client.create_review(
            installation_id=installation_id,
            repo_full_name=repo_full_name,
            pr_number=pr_number,
            head_sha=head_sha,
            body=review_body,
            comments=formatted_comments if formatted_comments else None,
            event='COMMENT',
        )
        
        if not success:
            logger.error(f"Failed to post review for PR #{pr_number}")
            # Try posting a simple comment as fallback
            github_client.create_comment(
                installation_id=installation_id,
                repo_full_name=repo_full_name,
                pr_number=pr_number,
                body=review_body,
            )
        
        # Step 7: Update check run to completed
        check_summary = review_formatter.format_check_run_summary(
            review_result=review_result,
            pr_info=pr_info,
            quick_warnings=quick_warnings,
        )
        
        github_client.create_check_run(
            installation_id=installation_id,
            repo_full_name=repo_full_name,
            head_sha=head_sha,
            name="AI Code Review",
            status="completed",
            conclusion="success",
            title=check_summary['title'],
            summary=check_summary['summary'],
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
            github_client.create_comment(
                installation_id=installation_id,
                repo_full_name=repo_full_name,
                pr_number=pr_number,
                body=error_comment,
            )
            
            # Update check run to failed
            github_client.create_check_run(
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


if __name__ == '__main__':
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

