"""
Firecrawl API wrapper with rate limit handling.
MATCHES YOUR NOTEBOOK LOGIC EXACTLY.
"""
from firecrawl import Firecrawl
from firecrawl.v2.utils.error_handler import RateLimitError
from config import settings
import time
import logging


class FirecrawlTool:
    """
    Wrapper for Firecrawl with retry logic.
    Matches notebook's scraping behavior with quota management.
    """
    
    def __init__(self):
        self.client = Firecrawl(api_key=settings.firecrawl_api_key)
        self.logger = logging.getLogger("tools.firecrawl")
        self.base_url = settings.firecrawl_base_url
        self.max_retries = settings.firecrawl_max_retries
    
    def get_quota(self, test_url: str = None) -> tuple:
        """
        Get current rate limit quota from headers.
        EXACT NOTEBOOK IMPLEMENTATION.
        
        Args:
            test_url: URL to test with (defaults to base_url)
            
        Returns:
            Tuple of (remaining_requests, reset_time_seconds)
        """
        test_url = test_url or self.base_url
        
        try:
            response = self.client.scrape(test_url, formats=["markdown"])
            headers = response.raw_response.headers
            
            remaining = int(headers.get("x-ratelimit-remaining", 1))
            reset = int(headers.get("x-ratelimit-reset", 0))
            
            self.logger.debug(f"Quota: {remaining} remaining, resets in {reset}s")
            return remaining, reset
        except Exception as e:
            self.logger.warning(f"Could not check quota: {e}")
            return None, None
    
    def enforce_quota(self, batch_size: int):
        """
        Proactively wait if quota is low before scraping.
        EXACT NOTEBOOK IMPLEMENTATION.
        
        Args:
            batch_size: Number of URLs about to scrape
        """
        remaining, reset = self.get_quota()
        
        if remaining is not None and remaining < batch_size:
            wait_time = reset + 1
            self.logger.warning(f"[QUOTA] Low quota ({remaining} < {batch_size}). Waiting {wait_time}s...")
            time.sleep(wait_time)
    
    def scrape(self, url: str, formats: list = None) -> dict:
        """
        Scrape URL with automatic retry on rate limit.
        MATCHES NOTEBOOK with safety limit to prevent infinite loops.
        
        Args:
            url: URL to scrape
            formats: List of formats (e.g., ["markdown", "links"])
            
        Returns:
            Dictionary with markdown and links
        """
        if formats is None:
            formats = ["markdown", "links"]
        
        # Safety counter (notebook has while True, but we add limit for production)
        max_attempts = self.max_retries * 10  # Much higher than 3, but not infinite
        attempt = 0
        
        while attempt < max_attempts:
            try:
                attempt += 1
                self.logger.info(f"Scraping {url} (attempt {attempt})")
                
                response = self.client.scrape(url, formats=formats)
                             
                links = []
                if hasattr(response, 'links') and response.links:
                    for link in response.links:
                        if isinstance(link, dict):
                            # Old API format: dict with "href" key
                            links.append(link.get("href", ""))
                        elif isinstance(link, str):
                            # New API format: direct string
                            links.append(link)
                        else:
                            # Fallback: convert to string
                            links.append(str(link))
                
                result = {
                    "markdown": response.markdown if hasattr(response, 'markdown') else "",
                    "links": links
                }
                
                self.logger.info(f"Successfully scraped {url}")
                return result
                
            except RateLimitError as e:
                # Get wait time from quota headers (notebook approach)
                remaining, reset = self.get_quota()
                wait_time = reset + 1 if reset else 20
                
                self.logger.warning(
                    f"Rate limited on {url}. "
                    f"Waiting {wait_time}s... (attempt {attempt}/{max_attempts})"
                )
                time.sleep(wait_time)
                
            except Exception as e:
                self.logger.error(f"Error scraping {url}: {e}")
                raise
        
        # If we exhaust all attempts (very unlikely with 30 tries)
        raise Exception(
            f"Failed to scrape {url} after {max_attempts} attempts. "
            f"This likely indicates a persistent API issue."
        )