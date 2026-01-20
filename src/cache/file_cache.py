"""File-based cache system with TTL support."""

from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any
import json
import logging


class FileCache:
    """File-based cache with timestamp validation."""
    
    def __init__(self, cache_dir: Path, ttl_days: int):
        """
        Initialize cache.
        
        Args:
            cache_dir: Directory for cache files
            ttl_days: Time-to-live in days
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_days = ttl_days
        self.logger = logging.getLogger("cache")
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def is_valid(self) -> bool:
        """
        Check if cache is still valid.
        
        Returns:
            True if cache exists and not expired
        """
        timestamp_file = self.cache_dir / ".timestamp"
        
        if not timestamp_file.exists():
            return False
        
        try:
            timestamp_str = timestamp_file.read_text().strip()
            timestamp = datetime.fromisoformat(timestamp_str)
            age = datetime.now() - timestamp
            
            is_valid = age.days < self.ttl_days
            
            if is_valid:
                self.logger.info(f"Cache valid (age: {age.days} days)")
            else:
                self.logger.info(f"Cache expired (age: {age.days} days, TTL: {self.ttl_days})")
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Error checking cache validity: {e}")
            return False
    
    def update_timestamp(self):
        """Update cache timestamp to now."""
        timestamp_file = self.cache_dir / ".timestamp"
        timestamp_file.write_text(datetime.now().isoformat())
        self.logger.info("Cache timestamp updated")
    
    def get_age(self) -> Optional[int]:
        """
        Get cache age in days.
        
        Returns:
            Age in days, or None if no timestamp
        """
        timestamp_file = self.cache_dir / ".timestamp"
        
        if not timestamp_file.exists():
            return None
        
        try:
            timestamp_str = timestamp_file.read_text().strip()
            timestamp = datetime.fromisoformat(timestamp_str)
            age = datetime.now() - timestamp
            return age.days
        except:
            return None
    
    def clear(self):
        """Clear all cache files."""
        import shutil
        
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info("Cache cleared")
    
    def save_json(self, filename: str, data: Any):
        """Save data as JSON."""
        filepath = self.cache_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved {filename}")
    
    def load_json(self, filename: str) -> Optional[Any]:
        """Load data from JSON."""
        filepath = self.cache_dir / filename
        
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading {filename}: {e}")
            return None
    
    def save_text(self, filename: str, content: str):
        """Save text content."""
        filepath = self.cache_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        filepath.write_text(content, encoding='utf-8')
        self.logger.info(f"Saved {filename}")
    
    def load_text(self, filename: str) -> Optional[str]:
        """Load text content."""
        filepath = self.cache_dir / filename
        
        if not filepath.exists():
            return None
        
        try:
            return filepath.read_text(encoding='utf-8')
        except Exception as e:
            self.logger.error(f"Error loading {filename}: {e}")
            return None