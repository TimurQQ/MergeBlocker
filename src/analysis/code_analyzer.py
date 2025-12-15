"""Code analyzer using LLM for PR review."""

import json
import logging
from typing import Any, Dict, List

from tenacity import before_sleep_log, retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from src.analysis.prompts import ReviewPrompts
from src.clients.llm_client import LLMClient

logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """Analyzes code changes using LLM (OpenRouter-compatible API)."""

    def __init__(self):
        self.client = LLMClient()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(0),
        retry=retry_if_exception_type((json.JSONDecodeError, ValueError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def analyze_pr(self, pr_context: Dict[str, Any], agents_md_content: str = None) -> Dict[str, Any]:
        """
        Analyze a Pull Request and generate review with inline comments.

        Retry logic:
            • JSONDecodeError, ValueError: LLM returned invalid JSON → retry (3 attempts)
            • No delay between retries (wait_fixed(0))

        Args:
            pr_context: Dictionary containing PR details from GitHub
            agents_md_content: Content of AGENTS.md file from repository (optional)

        Returns:
            Dictionary with review summary and inline comments

        Raises:
            json.JSONDecodeError: If LLM failed to return valid JSON after 3 attempts
        """
        pr = pr_context["pr"]
        files = pr_context["files"]

        # Build prompt with PR context and AGENTS.md
        prompt = self._build_review_prompt(pr, files, agents_md=agents_md_content)

        # Call LLM for detailed analysis
        try:
            review_text = self.client.generate(user_prompt=prompt, system_prompt=ReviewPrompts.SYSTEM_PROMPT)

            # Extract JSON from response (removes markdown blocks if present)
            json_text = self._extract_json_from_response(review_text)

            # Parse JSON - if invalid, will trigger retry
            result = json.loads(json_text)

            # Validate structure
            if not isinstance(result, dict):
                raise ValueError("LLM returned non-dict JSON")

            # Ensure required keys exist
            if "summary" not in result:
                raise ValueError("Missing 'summary' in LLM response")

            # Normalize structure
            return {
                "summary": result.get("summary", ""),
                "critical_issues": result.get("critical_issues", []),
                "suggestions": result.get("suggestions", []),
                "inline_comments": result.get("inline_comments", []),
            }

        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ Invalid JSON from LLM: {e}")
            logger.debug(f"Response was: {review_text[:500]}")
            # Re-raise for retry through tenacity
            raise
        except ValueError as e:
            logger.warning(f"⚠️ Invalid structure from LLM: {e}")
            # Re-raise for retry through tenacity
            raise
        except Exception as e:
            # Other errors (e.g., network issues) - don't retry, return error response
            logger.error(f"Error calling LLM: {e}")
            return self._get_error_response()

    def _build_review_prompt(self, pr: Dict[str, Any], files: List[Dict[str, Any]], agents_md: str = None) -> str:
        """Build prompt for detailed review with all changed files."""

        file_changes = []
        # Include all files with full patches
        for file in files:
            if file["patch"]:
                file_changes.append(
                    f"""
### File: {file['filename']} ({file['status']})
Changes: +{file['additions']} -{file['deletions']}

```diff
{file['patch']}
```
"""
                )

        changes_text = "\n".join(file_changes)

        return ReviewPrompts.get_detailed_review_prompt(pr, changes_text, agents_md=agents_md)

    def _extract_json_from_response(self, response: str) -> str:
        """
        Extract JSON from LLM response, removing markdown wrappers and comments.

        Handles cases:
        - ```json {...} ```
        - ``` {...} ```
        - {...}
        - Text before/after JSON

        Args:
            response: Raw response from LLM

        Returns:
            Cleaned JSON text
        """
        text = response.strip()

        # Remove markdown blocks
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first line (```json or ```)
            if lines[0].strip() in ["```json", "```"]:
                lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        # Find JSON object
        start_idx = text.find("{")
        end_idx = text.rfind("}")

        if start_idx != -1 and end_idx != -1:
            text = text[start_idx : end_idx + 1]

        return text

    def _get_error_response(self) -> Dict[str, Any]:
        """Return error response when analysis fails."""
        return {
            "summary": ReviewPrompts.get_error_response(),
            "inline_comments": [],
            "is_large_pr": False,
        }

    def quick_check(self, files: List[Dict[str, Any]]) -> List[str]:
        """
        Perform quick deterministic checks on files.

        Returns:
            List of warning messages
        """
        warnings = []

        # Check for potential secrets
        secret_patterns = ["api_key", "password", "secret", "token", "private_key"]
        for file in files:
            if file["patch"]:
                patch_lower = file["patch"].lower()
                for pattern in secret_patterns:
                    if pattern in patch_lower and "+" in file["patch"]:
                        warnings.append(f"⚠️ Potential secret detected in `{file['filename']}` " f"(pattern: {pattern})")
                        break

        # Check for TODOs in new code
        for file in files:
            if file["patch"] and ("TODO" in file["patch"] or "FIXME" in file["patch"]):
                if "+" in file["patch"]:  # Only in added lines
                    warnings.append(f"📝 TODO/FIXME found in `{file['filename']}`")

        return warnings
