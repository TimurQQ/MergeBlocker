"""
Промпты для LLM code review.
Все промпты вынесены в отдельный файл для удобства управления и версионирования.
"""

from typing import Any, Dict

from src.config import Config


class ReviewPrompts:
    """Коллекция промптов для code review."""

    # System prompts
    SYSTEM_SMALL_PR = "You are an expert code reviewer. Analyze the code changes and provide detailed, constructive feedback."

    SYSTEM_LARGE_PR = "You are an expert code reviewer. Provide a high-level summary for large PRs."

    @staticmethod
    def get_large_pr_prompt(pr: Dict[str, Any], stats: Dict[str, Any], file_list: str) -> str:
        """Промпт для анализа большого PR."""
        return f"""You are an AI code reviewer. Review this large Pull Request.

**PR Title:** {pr['title']}

**PR Description:**
{pr['body']}

**Statistics:**
- Files changed: {stats['total_files']}
- Lines added: {stats['total_additions']}
- Lines deleted: {stats['total_deletions']}

**Changed Files:**
{file_list}

This PR is too large for detailed review. Provide:
1. High-level summary of changes
2. Top 3-5 potential risks or concerns
3. Recommendations (suggest splitting if needed)

Format your response as:
## Summary
[summary here]

## Potential Risks
- [risk 1]
- [risk 2]

## Recommendations
- [recommendation 1]
- [recommendation 2]
"""

    @staticmethod
    def get_detailed_review_prompt(pr: Dict[str, Any], changes_text: str) -> str:
        """Промпт для детального review маленького PR."""
        return f"""You are an expert code reviewer. Review this Pull Request carefully.

**PR Title:** {pr['title']}

**PR Description:**
{pr['body'] or 'No description provided'}

**Author:** {pr['author']}
**Target Branch:** {pr['base_branch']}

**Changed Files:**
{changes_text}

Please provide a thorough code review with:

1. **Summary** (3-5 bullet points): Overview of changes and general assessment
2. **Critical Issues** (if any): Security vulnerabilities, bugs, breaking changes
3. **Suggestions** (3-7 items): Improvements for code quality, performance, or best practices
4. **Inline Comments** (up to {Config.MAX_INLINE_COMMENTS}): Specific issues in code with file path and line number

Focus on:
- Security issues (exposed secrets, vulnerabilities)
- Potential bugs and edge cases
- Code quality and maintainability
- Performance concerns
- Best practices for the language/framework
- Testing coverage

Format your response as:

## Summary
- [bullet point 1]
- [bullet point 2]

## Critical Issues
- [issue 1 if any]

## Suggestions
1. [suggestion 1]
2. [suggestion 2]

## Inline Comments
For each inline comment use this format:
FILE: path/to/file.py
LINE: 42
COMMENT: Your specific comment about this line

Be constructive and specific. Focus on the most important issues.
"""

    @staticmethod
    def get_error_response() -> str:
        """Текст ответа при ошибке анализа."""
        return """## AI Review Error

Unfortunately, the AI code review encountered an error. Please review this PR manually.

## Next Steps
- Check the application logs for details
- Ensure API keys are valid
- Verify the PR is not too large
"""
