"""
Agent 1: Scraper Agent
Scrapes IntentHQ website content with rate limit handling.
"""

from src.agents.base_agent import BaseAgent
from src.state.schemas import WorkflowState
from src.tools.firecrawl_tool import FirecrawlTool
from src.cache.file_cache import FileCache
from config import settings
import logging


class ScraperAgent(BaseAgent):
    """Scrapes IntentHQ website content and caches it."""
    
    def __init__(self):
        super().__init__(name="ScraperAgent")
        self.firecrawl = FirecrawlTool()
        self.cache = FileCache(
            cache_dir=settings.intenthq_cache_path,
            ttl_days=settings.intenthq_cache_ttl_days
        )
        self.base_url = settings.firecrawl_base_url
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Scrape IntentHQ website or load from cache.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with scraped content
        """
        self.log_execution_start()
        
        # Check cache first
        if self.cache.is_valid():
            self.logger.info("Using cached IntentHQ content")
            state["intenthq_content_raw"] = self._load_from_cache()
            state["intenthq_cache_hit"] = True
            self.update_state_metadata(state)
            return state
        
        self.logger.info("Cache expired or missing. Scraping IntentHQ website...")
        
        try:
            # Scrape main pages
            scraped_data = {
                "home": self.firecrawl.scrape(f"{self.base_url}/"),
                "platform": self.firecrawl.scrape(f"{self.base_url}/platform/"),
                "use_cases_root": self.firecrawl.scrape(f"{self.base_url}/use-cases/"),
                "about": self.firecrawl.scrape(f"{self.base_url}/about-us/"),
                "platform_items": {},
                "use_case_items": {}
            }
            
            # Extract and scrape platform links
            platform_links = self._extract_platform_links(scraped_data["platform"])
            for link in platform_links:
                slug = self._url_to_slug(link)
                self.logger.info(f"Scraping platform: {slug}")
                scraped_data["platform_items"][slug] = self.firecrawl.scrape(link)
            
            # Extract and scrape use case links
            usecase_links = self._extract_usecase_links(scraped_data["use_cases_root"])
            for link in usecase_links:
                slug = self._url_to_slug(link)
                self.logger.info(f"Scraping use case: {slug}")
                scraped_data["use_case_items"][slug] = self.firecrawl.scrape(link)
            
            # Save to cache
            self._save_to_cache(scraped_data)
            self.cache.update_timestamp()
            
            state["intenthq_content_raw"] = scraped_data
            state["intenthq_cache_hit"] = False
            
            self.update_state_metadata(state)
            self.log_execution_end(success=True)
            
            return state
            
        except Exception as e:
            self.log_error(e)
            self.add_error_to_state(state, f"Scraping failed: {str(e)}")
            raise
    
    def _extract_platform_links(self, platform_data: dict) -> list:
        """Extract platform product links."""
        links = platform_data.get("links", [])
        return [
            link for link in links
            if link.startswith(f"{self.base_url}/platform/")
            and link != f"{self.base_url}/platform/"
        ]
    
    def _extract_usecase_links(self, usecase_data: dict) -> list:
        """Extract use case links."""
        links = usecase_data.get("links", [])
        return [
            link for link in links
            if link.startswith(f"{self.base_url}/use-cases/")
            and link != f"{self.base_url}/use-cases/"
        ]
    
    def _url_to_slug(self, url: str) -> str:
        """Convert URL to filesystem-safe slug."""
        slug = url.replace(f"{self.base_url}/", "").strip("/")
        slug = slug.replace("/", "__")
        return slug or "index"
    
    def _save_to_cache(self, data: dict):
        """Save scraped data to cache."""
        self.cache.save_json("scraped_data.json", data)
        
        # Also save individual markdown files for easy access
        if "home" in data:
            self.cache.save_text("home.md", data["home"].get("markdown", ""))
        if "platform" in data:
            self.cache.save_text("platform.md", data["platform"].get("markdown", ""))
        if "about" in data:
            self.cache.save_text("about.md", data["about"].get("markdown", ""))
    
    def _load_from_cache(self) -> dict:
        """Load scraped data from cache."""
        return self.cache.load_json("scraped_data.json")