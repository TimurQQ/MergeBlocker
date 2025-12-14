"""Code analyzer using LLM for PR review."""
from typing import Dict, List, Any, Optional
from src.config import Config
from src.clients.llm_client import LLMClient
from src.analysis.prompts import ReviewPrompts


class CodeAnalyzer:
    """Analyzes code changes using LLM (OpenRouter-compatible API)."""
    
    def __init__(self):
        self.client = LLMClient()
    
    def analyze_pr(self, pr_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a Pull Request and generate review.
        
        Args:
            pr_context: Dictionary containing PR details from GitHub
        
        Returns:
            Dictionary with review summary and inline comments
        """
        pr = pr_context['pr']
        files = pr_context['files']
        stats = pr_context['stats']
        
        # Determine review strategy based on PR size
        if stats['total_files'] > Config.MAX_FILES_FOR_FULL_REVIEW or \
           stats['total_changes'] > Config.MAX_LINES_FOR_FULL_REVIEW:
            return self._analyze_large_pr(pr_context)
        else:
            return self._analyze_small_pr(pr_context)
    
    def _analyze_small_pr(self, pr_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze small PR with detailed inline comments."""
        pr = pr_context['pr']
        files = pr_context['files']
        
        # Build prompt with PR context
        prompt = self._build_review_prompt(pr, files, detailed=True)
        
        # Call LLM
        try:
            review_text = self.client.generate(
                user_prompt=prompt,
                system_prompt=ReviewPrompts.SYSTEM_SMALL_PR
            )
            
            # Parse response into structured format
            return self._parse_review_response(review_text, files)
            
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return self._get_error_response()
    
    def _analyze_large_pr(self, pr_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze large PR with summary only."""
        pr = pr_context['pr']
        files = pr_context['files']
        stats = pr_context['stats']
        
        # For large PRs, focus on high-level overview
        file_list = self._format_file_list(files)
        prompt = ReviewPrompts.get_large_pr_prompt(pr, stats, file_list)
        
        try:
            summary = self.client.generate(
                user_prompt=prompt,
                system_prompt=ReviewPrompts.SYSTEM_LARGE_PR
            )
            
            return {
                'summary': summary,
                'inline_comments': [],
                'is_large_pr': True,
            }
            
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return self._get_error_response()
    
    def _build_review_prompt(self, pr: Dict[str, Any], 
                            files: List[Dict[str, Any]], 
                            detailed: bool = True) -> str:
        """Build prompt for detailed review."""
        
        file_changes = []
        for file in files[:20]:  # Limit to first 20 files
            if file['patch']:
                file_changes.append(f"""
### File: {file['filename']} ({file['status']})
Changes: +{file['additions']} -{file['deletions']}

```diff
{file['patch'][:2000]}  
```
""")
        
        changes_text = "\n".join(file_changes)
        
        return ReviewPrompts.get_detailed_review_prompt(pr, changes_text)
    
    def _parse_review_response(self, review_text: str, 
                               files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse Claude's response into structured format."""
        
        # Extract inline comments
        inline_comments = []
        lines = review_text.split('\n')
        
        current_file = None
        current_line = None
        current_comment = []
        
        for line in lines:
            if line.startswith('FILE:'):
                if current_file and current_line and current_comment:
                    inline_comments.append({
                        'path': current_file,
                        'line': current_line,
                        'body': '\n'.join(current_comment).strip()
                    })
                current_file = line.replace('FILE:', '').strip()
                current_line = None
                current_comment = []
            elif line.startswith('LINE:'):
                try:
                    current_line = int(line.replace('LINE:', '').strip())
                except ValueError:
                    current_line = None
            elif line.startswith('COMMENT:'):
                current_comment = [line.replace('COMMENT:', '').strip()]
            elif current_file and current_line and line.strip():
                if not line.startswith('##') and not line.startswith('FILE:'):
                    current_comment.append(line)
        
        # Add last comment
        if current_file and current_line and current_comment:
            inline_comments.append({
                'path': current_file,
                'line': current_line,
                'body': '\n'.join(current_comment).strip()
            })
        
        # Limit inline comments
        inline_comments = inline_comments[:Config.MAX_INLINE_COMMENTS]
        
        return {
            'summary': review_text,
            'inline_comments': inline_comments,
            'is_large_pr': False,
        }
    
    def _format_file_list(self, files: List[Dict[str, Any]]) -> str:
        """Format file list for display."""
        lines = []
        for file in files:
            status_emoji = {
                'added': '➕',
                'modified': '📝',
                'removed': '❌',
                'renamed': '🔄',
            }.get(file['status'], '📄')
            
            lines.append(
                f"{status_emoji} `{file['filename']}` "
                f"(+{file['additions']} -{file['deletions']})"
            )
        
        return '\n'.join(lines)
    
    def _get_error_response(self) -> Dict[str, Any]:
        """Return error response when analysis fails."""
        return {
            'summary': ReviewPrompts.get_error_response(),
            'inline_comments': [],
            'is_large_pr': False,
        }
    
    def quick_check(self, files: List[Dict[str, Any]]) -> List[str]:
        """
        Perform quick deterministic checks on files.
        
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Check for potential secrets
        secret_patterns = ['api_key', 'password', 'secret', 'token', 'private_key']
        for file in files:
            if file['patch']:
                patch_lower = file['patch'].lower()
                for pattern in secret_patterns:
                    if pattern in patch_lower and '+' in file['patch']:
                        warnings.append(
                            f"⚠️ Potential secret detected in `{file['filename']}` "
                            f"(pattern: {pattern})"
                        )
                        break
        
        # Check for TODOs in new code
        for file in files:
            if file['patch'] and ('TODO' in file['patch'] or 'FIXME' in file['patch']):
                if '+' in file['patch']:  # Only in added lines
                    warnings.append(f"📝 TODO/FIXME found in `{file['filename']}`")
        
        # Check if PR is too large
        total_changes = sum(f['changes'] for f in files)
        if total_changes > Config.MAX_LINES_FOR_FULL_REVIEW:
            warnings.append(
                f"📊 Large PR: {total_changes} lines changed. "
                "Consider splitting into smaller PRs for better review."
            )
        
        return warnings

