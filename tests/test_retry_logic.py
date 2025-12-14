"""
Тесты для retry логики при работе с LLM.
Проверяет корректную обработку невалидного JSON.
"""

import json
from unittest.mock import patch

import pytest
from tenacity import RetryError

from src.analysis.code_analyzer import CodeAnalyzer


class TestRetryLogic:
    """Тесты для retry логики при парсинге JSON от LLM."""

    def test_valid_json_no_retry(self):
        """
        Тест: при валидном JSON retry не происходит.
        """
        analyzer = CodeAnalyzer()

        valid_json_response = json.dumps(
            {
                "summary": "Code looks good overall",
                "critical_issues": [],
                "suggestions": ["Consider adding tests"],
                "inline_comments": [{"path": "test.py", "line": 10, "body": "Good code"}],
            }
        )

        pr_context = {
            "pr": {
                "title": "Test PR",
                "body": "Test description",
                "author": "testuser",
                "base_branch": "main",
            },
            "files": [{"filename": "test.py", "status": "modified", "additions": 10, "deletions": 5, "patch": "test"}],
        }

        with patch.object(analyzer.client, "generate", return_value=valid_json_response) as mock_generate:
            result = analyzer.analyze_pr(pr_context)

            # Проверяем что вызвали LLM только 1 раз (без retry)
            assert mock_generate.call_count == 1

            # Проверяем структуру ответа
            assert "summary" in result
            assert "inline_comments" in result
            assert result["summary"] == "Code looks good overall"

    def test_invalid_json_with_retry(self):
        """
        Тест: при невалидном JSON происходят retry попытки.
        После 3 неудачных попыток должна быть ошибка.
        """
        analyzer = CodeAnalyzer()

        invalid_response = "This is not JSON at all"

        pr_context = {
            "pr": {
                "title": "Test PR",
                "body": "Test description",
                "author": "testuser",
                "base_branch": "main",
            },
            "files": [{"filename": "test.py", "status": "modified", "additions": 10, "deletions": 5, "patch": "test"}],
        }

        with patch.object(analyzer.client, "generate", return_value=invalid_response) as mock_generate:
            # Должна быть ошибка после 3 попыток
            with pytest.raises(RetryError):
                analyzer.analyze_pr(pr_context)

            # Проверяем что сделали 3 попытки
            assert mock_generate.call_count == 3

    def test_json_with_markdown_wrapper(self):
        """
        Тест: JSON в markdown блоках должен корректно извлекаться.
        """
        analyzer = CodeAnalyzer()

        markdown_wrapped_json = """```json
{
    "summary": "Test summary",
    "critical_issues": [],
    "suggestions": [],
    "inline_comments": []
}
```"""

        pr_context = {
            "pr": {
                "title": "Test PR",
                "body": "Test description",
                "author": "testuser",
                "base_branch": "main",
            },
            "files": [{"filename": "test.py", "status": "modified", "additions": 10, "deletions": 5, "patch": "test"}],
        }

        with patch.object(analyzer.client, "generate", return_value=markdown_wrapped_json) as mock_generate:
            result = analyzer.analyze_pr(pr_context)

            # Проверяем что вызвали LLM только 1 раз
            assert mock_generate.call_count == 1

            # Проверяем что JSON корректно распарсился
            assert result["summary"] == "Test summary"
            assert isinstance(result["inline_comments"], list)

    def test_retry_succeeds_on_second_attempt(self):
        """
        Тест: при первой неудаче и второй удаче, результат должен быть успешным.
        """
        analyzer = CodeAnalyzer()

        valid_json = json.dumps(
            {
                "summary": "Success on retry",
                "critical_issues": [],
                "suggestions": [],
                "inline_comments": [],
            }
        )

        pr_context = {
            "pr": {
                "title": "Test PR",
                "body": "Test description",
                "author": "testuser",
                "base_branch": "main",
            },
            "files": [{"filename": "test.py", "status": "modified", "additions": 10, "deletions": 5, "patch": "test"}],
        }

        # Первый вызов вернет невалидный JSON, второй - валидный
        with patch.object(analyzer.client, "generate", side_effect=["invalid json", valid_json]) as mock_generate:
            result = analyzer.analyze_pr(pr_context)

            # Проверяем что было 2 попытки
            assert mock_generate.call_count == 2

            # Проверяем успешный результат
            assert result["summary"] == "Success on retry"

    def test_missing_required_field_triggers_retry(self):
        """
        Тест: отсутствие обязательного поля 'summary' должно вызвать retry.
        """
        analyzer = CodeAnalyzer()

        # JSON без обязательного поля summary
        invalid_structure = json.dumps(
            {
                "critical_issues": [],
                "suggestions": [],
                "inline_comments": [],
            }
        )

        valid_json = json.dumps(
            {
                "summary": "Valid response after retry",
                "critical_issues": [],
                "suggestions": [],
                "inline_comments": [],
            }
        )

        pr_context = {
            "pr": {
                "title": "Test PR",
                "body": "Test description",
                "author": "testuser",
                "base_branch": "main",
            },
            "files": [{"filename": "test.py", "status": "modified", "additions": 10, "deletions": 5, "patch": "test"}],
        }

        with patch.object(analyzer.client, "generate", side_effect=[invalid_structure, valid_json]) as mock_generate:
            result = analyzer.analyze_pr(pr_context)

            # Проверяем что было 2 попытки
            assert mock_generate.call_count == 2

            # Проверяем успешный результат
            assert result["summary"] == "Valid response after retry"
