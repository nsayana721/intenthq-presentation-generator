"""
Agent 3: Query Generator Agent

"""
from src.agents.base_agent import BaseAgent
from src.state.schemas import WorkflowState, QueryGeneratorOutput, UseCaseQuery
from config.prompts import load_prompt
from datetime import datetime
import json


class QueryGeneratorAgent(BaseAgent):
    """Generates one Tavily query per use case (notebook logic)."""
    
    def __init__(self):
        super().__init__(name="QueryGeneratorAgent")
        self.prompt_template = load_prompt("query_generator.txt")
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Generate one query per use case.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with queries_json
        """
        self.log_execution_start()
        
        prospect_name = state["prospect_name"]
        cleaned_content = state.get("intenthq_content_cleaned", {})
        use_cases = cleaned_content.get("use_cases", [])
        
        if not use_cases:
            self.add_error_to_state(state, "No use cases found in cleaned content")
            raise ValueError("No use cases available")
        
        try:
            query_items = []
            total_tokens = 0
            
            # NOTEBOOK LOGIC: For each use case, generate one query
            for use_case in use_cases:
                usecase_slug = use_case.get("slug", "")
                usecase_content = use_case.get("content", "")
                
                self.logger.info(f"Generating query for: {usecase_slug}")
                
                # Generate query using LLM
                query = self._generate_single_query(
                    prospect_name=prospect_name,
                    usecase_content=usecase_content,
                    usecase_slug=usecase_slug
                )
                
                # Validate and truncate if needed
                if len(query) > 400:
                    self.logger.warning(f"Query too long ({len(query)} chars), truncating")
                    query = query[:400]
                
                query_items.append(UseCaseQuery(
                    usecase=usecase_slug,
                    query=query
                ))
                
                total_tokens += 100  # Approximate, track actual if needed
            
            # Build output matching notebook format
            output = QueryGeneratorOutput(
                brand=prospect_name,
                generated_at=datetime.utcnow().isoformat(),
                items=query_items
            )
            
            self.logger.info(f"Generated {len(query_items)} queries for {prospect_name}")
            
            # Save to state (matches schema)
            state["queries_json"] = output
            self.update_state_metadata(state, tokens=total_tokens)
            self.log_execution_end(success=True)
            
            return state
            
        except Exception as e:
            self.log_error(e)
            self.add_error_to_state(state, f"Query generation failed: {str(e)}")
            raise
    
    def _generate_single_query(self, prospect_name: str, usecase_content: str, usecase_slug: str) -> str:
        """
        Args:
            prospect_name: Brand/prospect name
            usecase_content: Use case markdown content
            usecase_slug: Use case identifier
            
        Returns:
            Optimized Tavily query string
        """
        # Format prompt with use case context
        prompt = self.prompt_template.format(
            prospect_name=prospect_name,
            brand=prospect_name,
            usecase_content=usecase_content[:3000],  # Limit context
            usecase_slug=usecase_slug
        )
        
        # Call LLM
        response = self.llm.invoke(prompt)
        
        # Extract query from response
        # Your notebook might return JSON or plain text - adjust as needed
        content = response.content.strip()
        
        # Try to parse as JSON first
        try:
            result = json.loads(content)
            query = result.get("query", content)
        except:
            # If not JSON, use raw content
            query = content
        
        return query