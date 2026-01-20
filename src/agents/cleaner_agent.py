"""
Agent 2: Cleaner Agent
Cleans scraped markdown content and organizes it.
"""

from src.agents.base_agent import BaseAgent
from src.state.schemas import WorkflowState
import re


class CleanerAgent(BaseAgent):
    """Cleans and organizes scraped content."""
    
    def __init__(self):
        super().__init__(name="CleanerAgent")
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Clean scraped content.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with cleaned content
        """
        self.log_execution_start()
        
        raw_content = state.get("intenthq_content_raw")
        if not raw_content:
            self.add_error_to_state(state, "No raw content to clean")
            raise ValueError("No raw content available")
        
        try:
            cleaned_content = {
                "home": self._clean_markdown(raw_content.get("home", {}).get("markdown", "")),
                "platform": self._clean_markdown(raw_content.get("platform", {}).get("markdown", "")),
                "about": self._clean_markdown(raw_content.get("about", {}).get("markdown", "")),
                "platform_products": [],
                "use_cases": []
            }
            
            # Clean platform items
            for slug, data in raw_content.get("platform_items", {}).items():
                cleaned_content["platform_products"].append({
                    "slug": slug,
                    "content": self._clean_markdown(data.get("markdown", ""))
                })
            
            # Clean use case items
            for slug, data in raw_content.get("use_case_items", {}).items():
                cleaned_content["use_cases"].append({
                    "slug": slug,
                    "content": self._clean_markdown(data.get("markdown", ""))
                })
            
            state["intenthq_content_cleaned"] = cleaned_content
            self.update_state_metadata(state)
            self.log_execution_end(success=True)
            
            return state
            
        except Exception as e:
            self.log_error(e)
            self.add_error_to_state(state, f"Cleaning failed: {str(e)}")
            raise
    
    def _clean_markdown(self, md: str) -> str:
        """Clean markdown content."""
        # Remove images
        md = re.sub(r"!\[.*?\]\(.*?\)", "", md)
        
        # Remove links but keep text
        md = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", md)
        
        # Remove standalone link references
        md = re.sub(r"^\s*\[.*?\]\s*$", "", md, flags=re.MULTILINE)
        
        # Remove deep headers (h4+)
        md = re.sub(r"^#{4,}.*$", "", md, flags=re.MULTILINE)
        
        # Normalize h3 to h2
        md = re.sub(r"^###\s*", "## ", md, flags=re.MULTILINE)
        
        # Remove numeric-only headers
        md = re.sub(r"^##\s*\d+\s*$", "", md, flags=re.MULTILINE)
        md = re.sub(r"^\s*\d+\s*$", "", md, flags=re.MULTILINE)
        
        # Remove horizontal rules
        md = re.sub(r"(\* \* \*|\*{3,}|-{3,})", "", md)
        
        # Remove CTAs
        cta_words = ["Book a Demo", "Learn more", "Download One-Pager", "Get Started"]
        for w in cta_words:
            md = re.sub(rf"^{w}.*$", "", md, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove footer patterns
        footer_patterns = [
            r"Sitemap", r"Privacy Policy", r"Website Terms",
            r"Legal", r"All Rights Reserved", r"© \d{4}"
        ]
        for p in footer_patterns:
            md = re.sub(rf".*{p}.*$", "", md, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove remaining bracket content
        md = re.sub(r"\[.*?\]", "", md)
        
        # Normalize whitespace
        md = re.sub(r"\n{3,}", "\n\n", md)
        
        return md.strip()