"""Integration tests for LLM code analysis."""

import pytest

from src.analysis.code_analyzer import CodeAnalyzer
from src.clients.llm_client import LLMClient


class TestLLMIntegration:
    """Integration tests that require LLM API access."""

    @pytest.fixture
    def llm_client(self, check_env_vars):
        """Create LLM client (requires API key)."""
        return LLMClient()

    @pytest.fixture
    def code_analyzer(self, check_env_vars):
        """Create code analyzer (requires API key)."""
        return CodeAnalyzer()

    def test_llm_client_creation(self, llm_client):
        """Test: LLM client is successfully created."""
        assert llm_client is not None
        assert llm_client.model is not None
        assert llm_client.api_key is not None
        print(f"\n✅ LLM Client created with model: {llm_client.model}")

    def test_simple_generation(self, llm_client):
        """Test: LLM can generate a simple response."""
        prompt = "Say 'Hello, MergeBlocker!' and nothing else."
        system_prompt = "You are a helpful assistant."

        response = llm_client.generate(user_prompt=prompt, system_prompt=system_prompt)

        assert response is not None
        assert len(response) > 0
        assert isinstance(response, str)
        print(f"\n✅ LLM generated response: {response[:100]}...")

    def test_code_review_generation(self, llm_client):
        """Test: LLM can generate code review feedback."""
        system_prompt = "You are a code reviewer. Provide brief feedback."
        user_prompt = """
        Review this code change:

        ```python
        def calculate_sum(a, b):
            return a + b
        ```

        Provide one sentence feedback.
        """

        review = llm_client.generate(user_prompt=user_prompt, system_prompt=system_prompt)

        assert review is not None
        assert len(review) > 0
        print(f"\n✅ Code review generated: {review[:200]}...")

    def test_small_pr_analysis(self, code_analyzer):
        """Test: Analyze a small PR (mock data)."""
        pr_context = {
            "pr": {
                "number": 1,
                "title": "Add helper function",
                "body": "This PR adds a simple helper function for calculations",
                "author": "test-user",
                "base_branch": "main",
            },
            "files": [
                {
                    "filename": "utils.py",
                    "status": "modified",
                    "additions": 5,
                    "deletions": 0,
                    "patch": '''@@ -10,0 +11,5 @@
+def calculate_sum(a, b):
+    """Calculate sum of two numbers."""
+    return a + b
+''',
                }
            ],
            "stats": {
                "total_files": 1,
                "total_additions": 5,
                "total_deletions": 0,
                "total_changes": 5,
            },
            "commits": [],
        }

        result = code_analyzer.analyze_pr(pr_context)

        assert result is not None
        assert "summary" in result
        assert "inline_comments" in result
        assert isinstance(result["summary"], str)
        assert isinstance(result["inline_comments"], list)
        print("\n✅ PR analysis completed")
        print(f"   Summary length: {len(result['summary'])} chars")
        print(f"   Inline comments: {len(result['inline_comments'])}")
        print(f"\n   Summary preview: {result['summary'][:200]}...")
