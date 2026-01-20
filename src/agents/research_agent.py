"""
Agent 4: Research Agent
Conducts prospect research using Tavily.
MATCHES NOTEBOOK: For each usecase-query pair, get Tavily answer.
"""

from src.agents.base_agent import BaseAgent
from src.state.schemas import WorkflowState, TavilyResearchOutput, UseCaseResearch
from src.tools.tavily_tool import TavilyTool
from src.cache.file_cache import FileCache
from config import settings
from datetime import datetime


class ResearchAgent(BaseAgent):
    """
    Researches prospect using Tavily.
    NOTEBOOK LOGIC: For each usecase-query, get AI answer (no synthesis).
    """
    
    def __init__(self):
        super().__init__(name="ResearchAgent")
        self.tavily = TavilyTool()
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute Tavily searches for each usecase-query pair.
        MATCHES NOTEBOOK EXACTLY.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with research_json
        """
        self.log_execution_start()
        
        prospect_name = state["prospect_name"]
        queries_json = state.get("queries_json")
        
        if not queries_json:
            self.add_error_to_state(state, "No queries available")
            raise ValueError("No queries_json in state")
        
        # Check cache first
        cache = self._get_client_cache(prospect_name)
        if cache.is_valid():
            self.logger.info("Using cached research data")
            cached = cache.load_json("research.json")
            if cached:
                state["research_json"] = TavilyResearchOutput(**cached)
                state["prospect_cache_hit"] = True
                self.update_state_metadata(state)
                return state
        
        self.logger.info(f"Researching {prospect_name} with {len(queries_json.items)} queries")
        
        try:
            research_items = []
            
            # NOTEBOOK LOGIC: For each usecase-query pair
            for query_item in queries_json.items:
                usecase = query_item.usecase
                query = query_item.query
                
                self.logger.info(f"[TAVILY] Searching for {usecase}...")
                
                # Call Tavily (returns {"answer": "..."})
                response = self.tavily.search(query)
                answer = response.get("answer", "")
                
                if not answer:
                    self.logger.warning(f"No answer for {usecase}")
                
                # Store usecase-answer pair (matches notebook)
                research_items.append(UseCaseResearch(
                    usecase=usecase,
                    answer=answer
                ))
            
            # Build output (matches notebook format)
            output = TavilyResearchOutput(
                brand=prospect_name,
                generated_at=datetime.utcnow().isoformat(),
                items=research_items
            )
            
            self.logger.info(f"Research complete: {len(research_items)} use cases")
            
            # Cache results
            cache.save_json("research.json", output.model_dump())
            cache.update_timestamp()
            
            # Save to state (matches schema)
            state["research_json"] = output
            state["prospect_cache_hit"] = False
            
            self.update_state_metadata(state)
            self.log_execution_end(success=True)
            
            return state
            
        except Exception as e:
            self.log_error(e)
            self.add_error_to_state(state, f"Research failed: {str(e)}")
            raise
    
    def _get_client_cache(self, client_name: str) -> FileCache:
        """Get cache for specific client."""
        cache_path = settings.get_client_cache_path(client_name)
        return FileCache(
            cache_dir=cache_path,
            ttl_days=settings.client_cache_ttl_days
        )