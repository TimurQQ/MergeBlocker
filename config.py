"""Configuration management for MergeBlocker."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration."""
    
    # GitHub App Settings
    GITHUB_APP_ID = os.getenv('GITHUB_APP_ID')
    GITHUB_PRIVATE_KEY_PATH = os.getenv('GITHUB_PRIVATE_KEY_PATH', './private-key.pem')
    GITHUB_WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET')
    
    # LLM Settings
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    
    # Server Settings
    PORT = int(os.getenv('PORT', 8000))
    HOST = os.getenv('HOST', '0.0.0.0')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Review Settings
    MAX_FILES_FOR_FULL_REVIEW = int(os.getenv('MAX_FILES_FOR_FULL_REVIEW', 20))
    MAX_LINES_FOR_FULL_REVIEW = int(os.getenv('MAX_LINES_FOR_FULL_REVIEW', 800))
    MAX_INLINE_COMMENTS = int(os.getenv('MAX_INLINE_COMMENTS', 10))
    SKIP_DRAFT_PRS = os.getenv('SKIP_DRAFT_PRS', 'True').lower() == 'true'
    
    @classmethod
    def get_private_key(cls) -> str:
        """Read and return the GitHub App private key."""
        key_path = Path(cls.GITHUB_PRIVATE_KEY_PATH)
        if not key_path.exists():
            raise FileNotFoundError(f"Private key not found at {key_path}")
        return key_path.read_text()
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        required = {
            'GITHUB_APP_ID': cls.GITHUB_APP_ID,
            'GITHUB_WEBHOOK_SECRET': cls.GITHUB_WEBHOOK_SECRET,
            'ANTHROPIC_API_KEY': cls.ANTHROPIC_API_KEY,
        }
        
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        # Check private key exists
        try:
            cls.get_private_key()
        except FileNotFoundError as e:
            raise ValueError(str(e))

