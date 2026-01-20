"""
Agent 7: Content Creator Agent
Generates presentation slides with specific prompts per slide type.

"""

from src.agents.base_agent import BaseAgent
from src.state.schemas import WorkflowState, ContentCreatorOutput, SlideContent
from config.prompts import load_prompt
from datetime import datetime
import json
import re


class ContentCreatorAgent(BaseAgent):
    """
    Creates presentation content slide by slide.
    
    """
    
    def __init__(self):
        super().__init__(name="ContentCreatorAgent", temperature=0.1)  # Match notebook
        self.slide3_prompt = load_prompt("industry_slide.txt")
        self.pain_prompt = load_prompt("pain_slides.txt")
        self.primary_solution_prompt = load_prompt("primary_solution.txt")
        self.secondary_solution_prompt = load_prompt("secondary_solution.txt")
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Generate slide content.
                
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with content_json
        """
        self.log_execution_start()
        
        prospect_name = state["prospect_name"]
        top_3_usecases = state.get("top_3_usecases")
        research_json = state.get("research_json")
        product_mapping_json = state.get("product_mapping_json")
        intenthq_content = state.get("intenthq_content_cleaned", {})
        
        if not all([top_3_usecases, research_json, product_mapping_json]):
            self.add_error_to_state(state, "Missing required data for content generation")
            raise ValueError("Incomplete data")
        
        try:
            # Build maps (notebook logic)
            answer_map = {item.usecase: item.answer for item in research_json.items}
            solution_map = {s.usecase: s for s in product_mapping_json.solutions}
            
            # Load products markdown
            products = self._load_products(intenthq_content)
            
            total_tokens = 0
            
            # Generate slide 3 (industry context)
            self.logger.info("[SLIDE 3] Generating industry context...")
            slide3 = self._gen_slide3(top_3_usecases, answer_map, prospect_name)
            total_tokens += 200
            
            # Generate slides 4-6 (pain slides)
            pain_slides = []
            for usecase in top_3_usecases:
                self.logger.info(f"[PAIN SLIDE] Generating for {usecase}...")
                pain_slide = self._gen_pain_slide(usecase, answer_map[usecase])
                pain_slides.append(pain_slide)
                total_tokens += 200
            
            # Generate slides 10-11 (solution slides)
            self.logger.info("[SOLUTION SLIDES] Generating product solutions...")
            primary_slide, secondary_slide = self._gen_solution_slides(
                top_3_usecases=top_3_usecases,
                solution_map=solution_map,
                answer_map=answer_map,
                products=products
            )
            total_tokens += 400
            
            # Build complete deck (notebook structure)
            deck_slides = self._build_deck(
                brand=prospect_name,
                slide3=slide3,
                pain_slides=pain_slides,
                top_3_usecases=top_3_usecases,
                primary_slide=primary_slide,
                secondary_slide=secondary_slide
            )
            
            # Build output (matches schema)
            output = ContentCreatorOutput(
                brand=prospect_name,
                generated_at=datetime.utcnow().isoformat(),
                slides=deck_slides
            )
            
            self.logger.info(f"Generated {len(deck_slides)} slides")
            
            # Save to state (matches schema)
            state["content_json"] = output
            self.update_state_metadata(state, tokens=total_tokens)
            self.log_execution_end(success=True)
            
            return state
            
        except Exception as e:
            self.log_error(e)
            self.add_error_to_state(state, f"Content generation failed: {str(e)}")
            raise
    
    def _gen_slide3(self, top_3_usecases: list, answer_map: dict, brand: str) -> dict:
        """
        Generate slide 3 (Industry & Prospect Context).
        EXACT NOTEBOOK FUNCTION.
        """
        # Build evidence block
        block = ""
        for u in top_3_usecases:
            block += f"\nUSECASE: {u}\n{answer_map[u]}\n"
        
        # Build prompt
        prompt = f"""{self.slide3_prompt}

Brand: {brand}
Evidence:
{block}
"""
        
        # Call LLM
        response = self.llm.invoke(prompt)
        raw = response.content
        
        # Parse JSON (with fallback)
        try:
            return json.loads(raw)
        except:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            return json.loads(match.group(0))
    
    def _gen_pain_slide(self, usecase: str, answer: str) -> dict:
        """
        Generate pain slide for single use case.
        EXACT NOTEBOOK FUNCTION.
        """
        prompt = f"""{self.pain_prompt}

Usecase: {usecase}
Evidence:
{answer}
"""
        
        response = self.llm.invoke(prompt)
        raw = response.content
        
        try:
            return json.loads(raw)
        except:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            return json.loads(match.group(0))
    
    def _gen_solution_slides(self, top_3_usecases: list, solution_map: dict, 
                            answer_map: dict, products: dict) -> tuple:
        """
        Generate solution slides (primary + secondary).
        EXACT NOTEBOOK FUNCTION gen_solution_slide().
        """
        # Build product coverage map (notebook logic)
        coverage = {}
        for u in top_3_usecases:
            sols = solution_map[u].products
            for p in sols:
                name = p.name
                if name not in coverage:
                    coverage[name] = {
                        "usecases": [],
                        "roles": [],
                        "brand_value": solution_map[u].brand_value
                    }
                coverage[name]["usecases"].append(u)
                coverage[name]["roles"].append(p.role)
        
        # Sort by coverage (most use cases = primary)
        sorted_products = sorted(
            coverage.items(),
            key=lambda kv: len(kv[1]["usecases"]),
            reverse=True
        )
        
        primary_name, primary_info = sorted_products[0]
        secondary = sorted_products[1:]
        
        # Generate primary product slide
        pain_block = ""
        for u in primary_info["usecases"]:
            pain_block += f"\nUSECASE: {u}\nPainEvidence:\n{answer_map[u]}\n"
        
        primary_md = products.get(primary_name, "")
        
        primary_prompt = f"""{self.primary_solution_prompt}

Brand pains:
{pain_block}

Product: {primary_name}

ProductMarkdown:
{primary_md}

BrandValue: {primary_info['brand_value']}
"""
        
        primary_response = self.llm.invoke(primary_prompt)
        primary_slide = json.loads(primary_response.content)
        
        # Generate secondary slide (if any)
        secondary_slide = None
        if secondary:
            sec_block = ""
            for name, _info in secondary:
                sec_block += f"\nSecondaryProduct: {name}\nProvidedRoles:{_info['roles']}\n"
            
            secondary_prompt = f"""{self.secondary_solution_prompt}

Brand: pains for top3 usecases:
{pain_block}

Secondary Details:
{sec_block}
"""
            
            secondary_response = self.llm.invoke(secondary_prompt)
            secondary_slide = json.loads(secondary_response.content)
        
        return primary_slide, secondary_slide
    
    def _build_deck(self, brand: str, slide3: dict, pain_slides: list,
                   top_3_usecases: list, primary_slide: dict, secondary_slide: dict) -> list:
        """
        Build complete slide deck.
        EXACT NOTEBOOK STRUCTURE.
        """
        slides = []
        
        # Slide 1: Title
        slides.append(SlideContent(
            slide=1,
            title=f"Intent HQ x {brand}",
            content=""
        ))
        
        # Slide 2: Agenda
        slides.append(SlideContent(
            slide=2,
            title="Agenda",
            bullets=["The Shift",
                     "The Challenge",
                     "About IntentHQ",
                     "Platform Overview",
                     "The Solution",
                     "AoB & Next steps"]
        ))
        
        # Slide 3: Industry Context
        slides.append(SlideContent(
            slide=3,
            title="Industry & Prospect Context",
            content=slide3.get("content"),
            bullets=slide3.get("bullets")
        ))
        
        # Slides 4-6: Pain slides
        for idx, usecase in enumerate(top_3_usecases):
            slides.append(SlideContent(
                slide=4 + idx,
                title=pain_slides[idx].get("title"),
                bullets=pain_slides[idx].get("bullets")
            ))
        
        # Slide 7: About Intent HQ (STATIC)
        slides.append(SlideContent(
            slide=7,
            title="About Intent HQ",
            content="STATIC_TEMPLATE"
        ))
        
        # Slide 8: About the Intent HQ(cont..d) (STATIC)
        slides.append(SlideContent(
            slide=8,
            title="About the Intent HQ(cont..d)",
            content="STATIC_TEMPLATE"
        ))
        
        # Slide 9: Platform Overview (STATIC)
        slides.append(SlideContent(
            slide=9,
            title="Platform Overview",
            content="STATIC_TEMPLATE"
        ))
        
        # Slide 10: Primary Product Solution
        slides.append(SlideContent(
            slide=10,
            title="Primary Product Solution",
            bullets=primary_slide.get("bullets")
        ))
        
        # Slide 11: Secondary Products (if exists)
        if secondary_slide:
            slides.append(SlideContent(
                slide=11,
                title="Complementary Product Solutions",
                bullets=secondary_slide.get("bullets")
            ))
        
        # Slide 12: AOB & Next Steps (STATIC)
        slides.append(SlideContent(
            slide=12,
            title="AOB & Next Steps",
            content="STATIC_TEMPLATE"
        ))
        
        return slides
    
    def _load_products(self, intenthq_content: dict) -> dict:
        """Load products markdown content."""
        products = {}
        for product in intenthq_content.get("platform_products", []):
            slug = product.get("slug", "")
            content = product.get("content", "")
            if slug and content:
                products[slug] = content
        return products