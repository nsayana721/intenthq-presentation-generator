"""
Settings management using Pydantic.
Loads configuration from environment variables.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    openai_api_key: str
    firecrawl_api_key: str
    tavily_api_key: str
    
    # Model Configuration
    llm_model: str = "gpt-5.2"
    llm_temperature: float = 0.1
    
    # Cache Configuration
    intenthq_cache_ttl_days: int = 14
    client_cache_ttl_days: int = 3
    
    # Paths (relative to project root)
    data_dir: Path = Path("data")
    cache_dir: Path = Path("data/cache")
    templates_dir: Path = Path("data/templates")
    outputs_dir: Path = Path("data/outputs")
    logs_dir: Path = Path("logs")
    
    
    # Firecrawl Configuration
    firecrawl_base_url: str = "https://intenthq.com"
    firecrawl_max_retries: int = 3
    
    # Tavily Configuration
    tavily_max_results: int = 5
    tavily_query_max_length: int = 400
    
    # UI Configuration
    streamlit_port: int = 8501
    streamlit_theme: str = "light"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def intenthq_cache_path(self) -> Path:
        """Path to IntentHQ content cache."""
        return self.cache_dir / "intenthq_content"
    
    @property
    def clients_cache_path(self) -> Path:
        """Path to client research cache."""
        return self.cache_dir / "clients"
    
    @property
    def template_path(self) -> Path:
        """Path to PPTX template."""
        return self.templates_dir / "intenthq_template.pptx"
    
    def get_client_cache_path(self, client_name: str) -> Path:
        """Get cache path for specific client."""
        # Sanitize client name for filesystem
        safe_name = "".join(c for c in client_name if c.isalnum() or c in (' ', '-', '_'))
        safe_name = safe_name.replace(' ', '_')
        return self.clients_cache_path / safe_name
    
    def ensure_directories(self):
        """Create all required directories if they don't exist."""
        directories = [
            self.data_dir,
            self.cache_dir,
            self.intenthq_cache_path,
            self.clients_cache_path,
            self.templates_dir,
            self.outputs_dir,
            self.logs_dir,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
            # Create .gitkeep in empty directories
            gitkeep = directory / ".gitkeep"
            if not any(directory.iterdir()) and not gitkeep.exists():
                gitkeep.touch()


# Global settings instance
settings = Settings()

# Ensure directories exist on import
settings.ensure_directories()