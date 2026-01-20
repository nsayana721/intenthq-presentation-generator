"""
Agent 6: Product Mapper Agent
Maps IntentHQ products to selected use cases.

"""

from src.agents.base_agent import BaseAgent
from src.state.schemas import WorkflowState, ProductMappingOutput, UseCaseSolution, ProductSolution
from config.prompts import load_prompt
from datetime import datetime
import json
import re


class ProductMapperAgent(BaseAgent):
    """
    Maps IntentHQ products to top 3 use cases.
    
    """
    
    def __init__(self):
        super().__init__(name="ProductMapperAgent", temperature=0.1)  # Match notebook
        self.prompt = load_prompt("product_mapper.txt")
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Map products to selected use cases.
    
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with product_mapping_json
        """
        self.log_execution_start()
        
        prospect_name = state["prospect_name"]
        
        # Get top 3 use cases (from human checkpoint)
        top_3_usecases = state.get("top_3_usecases")
        if not top_3_usecases or len(top_3_usecases) == 0:
            self.add_error_to_state(state, "No use cases selected")
            raise ValueError("top_3_usecases is empty - human checkpoint not completed")
        
        # Get research data (to fetch Tavily answers)
        research_json = state.get("research_json")
        if not research_json:
            self.add_error_to_state(state, "No research data available")
            raise ValueError("Missing research_json")
        
        # Build map of usecase -> answer (notebook logic)
        web_map = {item.usecase: item.answer for item in research_json.items}
        
        # Get IntentHQ products
        intenthq_content = state.get("intenthq_content_cleaned", {})
        products = self._load_products(intenthq_content)
        
        if not products:
            self.add_error_to_state(state, "No products found")
            raise ValueError("No IntentHQ products available")
        
        try:
            solutions = []
            total_tokens = 0
            
            # NOTEBOOK LOGIC: For each selected use case
            for usecase in top_3_usecases:
                self.logger.info(f"[SOLVING] {usecase}")
                
                # Get Tavily answer for this use case
                answer_text = web_map.get(usecase, "")
                
                if not answer_text:
                    self.logger.warning(f"No research answer for {usecase}")
                
                # Map products to this use case (one LLM call)
                solution = self._solve_usecase(
                    usecase=usecase,
                    answer_text=answer_text,
                    products=products
                )
                
                solutions.append(solution)
                total_tokens += 300  # Approximate
            
            # Build output (matches notebook format)
            output = ProductMappingOutput(
                brand=prospect_name,
                generated_at=datetime.utcnow().isoformat(),
                solutions=solutions
            )
            
            self.logger.info(f"Mapped products for {len(solutions)} use cases")
            
            # Save to state (matches schema)
            state["product_mapping_json"] = output
            self.update_state_metadata(state, tokens=total_tokens)
            self.log_execution_end(success=True)
            
            return state
            
        except Exception as e:
            self.log_error(e)
            self.add_error_to_state(state, f"Product mapping failed: {str(e)}")
            raise
    
    def _solve_usecase(self, usecase: str, answer_text: str, products: dict) -> UseCaseSolution:
        """
        Map products to single use case.
        
        Args:
            usecase: Use case slug
            answer_text: Tavily answer (pain evidence)
            products: Dictionary of product_slug -> markdown content
            
        Returns:
            UseCaseSolution with products mapped
        """
        # Format products for LLM (notebook format)
        prod_block = ""
        for slug, md in products.items():
            prod_block += f"\n\n### PRODUCT {slug}\n{md.strip()}\n"
        
        # Build prompt (exact notebook format)
        prompt = f"""{self.prompt}

Usecase: {usecase}

Pain Evidence:
{answer_text}

Products:
{prod_block}

Now produce the JSON.
"""
        
        # Call LLM
        response = self.llm.invoke(prompt)
        raw = response.content.strip()
        
        # Parse JSON (with notebook's fallback logic)
        try:
            parsed = json.loads(raw)
        except:
            # Soft recovery if extra text exists (notebook logic)
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                raise ValueError(f"Could not parse JSON for {usecase}: {raw}")
            parsed = json.loads(match.group(0))
        
        # Convert to schema format
        products_list = [
            ProductSolution(
                name=p.get("name", ""),
                role=p.get("role", "")
            )
            for p in parsed.get("products", [])
        ]
        
        return UseCaseSolution(
            usecase=parsed.get("usecase", usecase),
            products=products_list,
            brand_value=parsed.get("brand_value", "")
        )
    
    def _load_products(self, intenthq_content: dict) -> dict:
        """
           
        Args:
            intenthq_content: Cleaned IntentHQ content
            
        Returns:
            Dictionary of product_slug -> markdown content
        """
        products = {}
        
        for product in intenthq_content.get("platform_products", []):
            slug = product.get("slug", "")
            content = product.get("content", "")
            
            if slug and content:
                products[slug] = content
        
        return products