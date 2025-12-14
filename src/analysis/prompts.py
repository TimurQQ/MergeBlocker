"""
Промпты для LLM code review.
Все промпты вынесены в отдельный файл для удобства управления и версионирования.
"""

from typing import Any, Dict


class ReviewPrompts:
    """Коллекция промптов для code review."""

    # System prompt
    SYSTEM_PROMPT = """You are an expert code reviewer. Analyze the code changes and provide detailed, constructive feedback.
Your goal is to help improve code quality while being respectful and educational."""

    @staticmethod
    def get_detailed_review_prompt(pr: Dict[str, Any], changes_text: str, agents_md: str = None) -> str:
        """Промпт для детального review маленького PR."""
        agents_section = ""
        if agents_md:
            agents_section = f"""
**Project Guidelines (from AGENTS.md):**
```
{agents_md[:3000]}
```

IMPORTANT: Follow the guidelines from AGENTS.md when reviewing this code.
"""

        return f"""You are an expert code reviewer. Review this Pull Request carefully.

**PR Title:** {pr['title']}

**PR Description:**
{pr['body'] or 'No description provided'}

**Author:** {pr['author']}
**Target Branch:** {pr['base_branch']}
{agents_section}
**Changed Files:**
{changes_text}

Please provide a thorough code review focusing on:
- **Guidelines from AGENTS.md** (if provided above)
- Security issues (exposed secrets, vulnerabilities)
- Potential bugs and edge cases
- Code quality and maintainability
- Performance concerns
- Best practices for the language/framework
- Testing coverage

**IMPORTANT**: Return your response as a valid JSON object with this exact structure:

{{
  "summary": "Overall assessment of the PR in 3-5 sentences",
  "critical_issues": [
    "Critical issue 1",
    "Critical issue 2"
  ],
  "suggestions": [
    "Suggestion 1",
    "Suggestion 2"
  ],
  "inline_comments": [
    {{
      "path": "src/api.py",
      "line": 42,
      "body": "🐛 Specific comment about this line"
    }},
    {{
      "path": "src/utils.py",
      "line": 15,
      "body": "⚡ Performance: Consider using dict.get() instead"
    }}
  ]
}}

**CRITICAL REQUIREMENTS**:
1. Response must be ONLY valid JSON (no markdown, no ```json blocks)
2. Create specific inline_comments for actual code issues (point to exact lines!)
3. Each inline comment must have: path (string), line (integer), body (string)
4. If no critical issues, use empty array: "critical_issues": []
5. Be constructive and specific in all comments
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
