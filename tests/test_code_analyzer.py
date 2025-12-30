"""Tests for CodeAnalyzer."""

import pytest

from src.analysis.code_analyzer import CodeAnalyzer


class TestCodeAnalyzer:
    """Test suite for CodeAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create CodeAnalyzer instance."""
        return CodeAnalyzer()

    def test_add_line_numbers_to_patch_simple(self, analyzer):
        """Test adding line numbers to a simple patch."""
        patch = """@@ -28,1 +26,4 @@
-private val userId: Int = prefs.getInt(USER_ID_KEY, -1)
+private var currentIndex = 0
+private val loadThreshold = 20
+private val pageSize = 200"""

        result = analyzer._add_line_numbers_to_patch(patch)

        # Check that header is preserved
        assert "@@ -28,1 +26,4 @@" in result

        # Check that removed line has no number (line starting with - should not have number prefix)
        assert "-private val userId" in result
        # Make sure the removed line doesn't have a number prefix
        lines = result.split("\n")
        for line in lines:
            if line.startswith("-private val userId"):
                # This line should NOT have a number prefix like "28: -"
                assert not line[0].isdigit(), f"Removed line should not have number prefix: {line}"

        # Check that added lines have correct numbers
        assert "26: +private var currentIndex = 0" in result
        assert "27: +private val loadThreshold = 20" in result
        assert "28: +private val pageSize = 200" in result

    def test_add_line_numbers_to_patch_with_context(self, analyzer):
        """Test adding line numbers with context lines."""
        # Note: Empty line has a space prefix (Git diff format for empty context lines)
        patch = (
            "@@ -10,5 +10,6 @@\n"
            " function calculate() {\n"
            "     const x = 1;\n"
            "+    const y = 2;\n"
            "     const z = 3;\n"
            " \n"  # Empty line with space prefix
            "     return x + z;"
        )

        result = analyzer._add_line_numbers_to_patch(patch)

        # Context lines should have numbers
        assert "10:  function calculate() {" in result
        assert "11:      const x = 1;" in result

        # Added line should have correct number
        assert "12: +    const y = 2;" in result

        # Following context should continue numbering
        assert "13:      const z = 3;" in result
        assert "14:  " in result  # Empty line with space prefix
        assert "15:      return x + z;" in result

    def test_add_line_numbers_to_patch_multiple_hunks(self, analyzer):
        """Test adding line numbers to patch with multiple hunks."""
        patch = """@@ -10,3 +10,4 @@
 line 10
+line 11 added
 line 12
 line 13
@@ -50,2 +51,3 @@
 line 51
+line 52 added
 line 53"""

        result = analyzer._add_line_numbers_to_patch(patch)

        # First hunk
        assert "10:  line 10" in result
        assert "11: +line 11 added" in result
        assert "12:  line 12" in result
        assert "13:  line 13" in result

        # Second hunk (starts at line 51)
        assert "51:  line 51" in result
        assert "52: +line 52 added" in result
        assert "53:  line 53" in result

    def test_add_line_numbers_to_patch_only_additions(self, analyzer):
        """Test patch with only additions (new file or large addition)."""
        patch = """@@ -0,0 +1,3 @@
+def new_function():
+    return True
+"""

        result = analyzer._add_line_numbers_to_patch(patch)

        assert "1: +def new_function():" in result
        assert "2: +    return True" in result
        assert "3: +" in result

    def test_add_line_numbers_to_patch_only_deletions(self, analyzer):
        """Test patch with only deletions."""
        patch = """@@ -10,3 +10,0 @@
-def old_function():
-    return False
-"""

        result = analyzer._add_line_numbers_to_patch(patch)

        # Removed lines should not have numbers in new version
        assert "-def old_function():" in result
        assert "-    return False" in result
        # Make sure we didn't add numbers to removed lines
        assert "10: -" not in result

    def test_add_line_numbers_preserves_empty_lines(self, analyzer):
        """Test that empty lines and special markers are preserved."""
        # Note: Empty line has a space prefix (Git diff format)
        patch = (
            "@@ -10,4 +10,4 @@\n"
            " line 10\n"
            " \n"  # Empty line with space prefix
            " line 12\n"
            "\\ No newline at end of file"
        )

        result = analyzer._add_line_numbers_to_patch(patch)

        # Empty line should still get a number
        assert "10:  line 10" in result
        assert "11:  " in result  # Empty context line with space prefix
        assert "12:  line 12" in result

        # Special marker should be preserved without number
        assert "\\ No newline at end of file" in result
        assert "13: \\" not in result  # No number for special markers

    def test_add_line_numbers_real_example(self, analyzer):
        """Test with real-world example - multiple hunks with additions and deletions."""
        # Note: Empty line has a space prefix (Git diff format)
        patch = (
            "@@ -28,1 +26,4 @@ class DataManager {\n"
            "-    this.userId = getUserId();\n"
            "+    this.currentIndex = 0;\n"
            "+    this.loadThreshold = 20;\n"
            "+    this.pageSize = 200;\n"
            " \n"  # Empty line with space prefix
            "@@ -31,0 +32,1 @@ class DataManager {\n"
            "+        this.loadData(true);"
        )

        result = analyzer._add_line_numbers_to_patch(patch)

        # First hunk: line 28 removed, lines 26-28 added
        assert "-    this.userId = getUserId();" in result
        assert "26: +    this.currentIndex = 0;" in result
        assert "27: +    this.loadThreshold = 20;" in result
        assert "28: +    this.pageSize = 200;" in result
        assert "29:  " in result  # Context line after additions (empty line with space)

        # Second hunk: line 32 added
        assert "32: +        this.loadData(true);" in result
