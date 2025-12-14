"""
Промпты для LLM code review.
Все промпты вынесены в отдельный файл для удобства управления и версионирования.
"""

from typing import Any, Dict


class ReviewPrompts:
    """Коллекция промптов для code review."""

    # System prompt
    SYSTEM_PROMPT = """You are an expert code reviewer. Analyze the code changes and provide detailed, constructive feedback.

**Your review style:**
- Be SPECIFIC and ACTIONABLE - always show exact code examples in the language being reviewed
- Point to exact lines with issues and provide code snippets to fix them
- Never use vague suggestions like "consider", "maybe", "might want to" without showing HOW
- Always include: 1) Current problematic code, 2) Why it's a problem, 3) Exact code to fix it
- Use code blocks with proper syntax highlighting
- Be respectful and educational, but concrete

**Example of GOOD feedback:**
"🐛 Missing null check. Current code will crash if value is null/nil/None. Show the exact fix with a code snippet."

**Example of BAD feedback (too vague):**
"Consider adding validation" ❌

Your goal is to help developers understand the exact changes they need to make."""

    @staticmethod
    def get_detailed_review_prompt(pr: Dict[str, Any], changes_text: str, agents_md: str = None) -> str:
        """Промпт для детального review маленького PR."""
        agents_section = ""
        if agents_md:
            # Include full AGENTS.md (LLM will handle context window)
            agents_section = f"""
**Project Guidelines (from AGENTS.md):**
```
{agents_md}
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
      "path": "src/file.ext",
      "line": 42,
      "body": "🐛 **Bug: Missing null check**\\n\\n
Current code:\\n```\\nresult = data[key]\\n```\\n\\n
Problem: Will crash if key doesn't exist.\\n\\n
Recommended fix:\\n```\\n
if (key in data) {{\\n  result = data[key]\\n}}
else {{\\n  result = defaultValue\\n}}\\n```"
    }},
    {{
      "path": "src/another.ext",
      "line": 15,
      "body": "⚡ **Performance improvement**\\n\\n
Current implementation has O(n²) complexity.\\n\\n
Show the optimized code with explanation."
    }}
  ]
}}

**CRITICAL REQUIREMENTS FOR INLINE COMMENTS**:
1. Response must be ONLY valid JSON (no markdown, no ```json blocks)
2. Create specific inline_comments for actual code issues (point to exact lines!)
3. Each inline comment MUST include:
   - **Issue description** with emoji (🐛 bug, ⚡ performance, 🔒 security, ♻️ refactor, 📝 style)
   - **Current code snippet** showing the problematic code
   - **Explanation** of why it's an issue
   - **Recommended fix** with actual code example
4. Use code blocks in comments: \\n```language\\ncode here\\n```\\n
5. Be SPECIFIC and ACTIONABLE - show exact code to write, not vague suggestions
6. If no critical issues, use empty array: "critical_issues": []
7. Escape all quotes and newlines in JSON properly

**BAD EXAMPLE** (vague, no code):
"body": "Consider adding error handling" ❌

**GOOD EXAMPLE** (specific, with code):
"body": "🐛 **Missing error handling**\\n\\n
Current code will crash on network errors.\\n\\n
Add error handling:\\n```\\n
try {{\\n  response = fetch(url)\\n  return response.data\\n}}
catch (error) {{\\n  logError(error)\\n  return null\\n}}\\n```"
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
