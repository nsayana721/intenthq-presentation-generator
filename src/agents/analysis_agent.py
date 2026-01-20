"""
Agent 5: Analysis Agent
Scores use cases based on pain/opportunity fit.
MATCHES NOTEBOOK EXACTLY + Enhanced sorting + Table display.
"""

from src.agents.base_agent import BaseAgent
from src.state.schemas import WorkflowState, AnalysisOutput, UseCaseScore
from config.prompts import load_prompt
from datetime import datetime
import json
import re


class AnalysisAgent(BaseAgent):
    """
    Analyzes use case fit for prospect.
    NOTEBOOK LOGIC: For each usecase-answer, score pain + 4 dimensions.
    """
    
    # Weights from notebook
    W_COST = 0.40
    W_BENCH = 0.30
    W_PRESS = 0.20
    W_PRIV = 0.10
    
    def __init__(self):
        super().__init__(name="AnalysisAgent", temperature=0.1)  # Match notebook
        self.prompt = load_prompt("analysis.txt")
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Score each use case based on Tavily research.
        MATCHES NOTEBOOK EXACTLY.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with analysis_json
        """
        self.log_execution_start()
        
        prospect_name = state["prospect_name"]
        research_json = state.get("research_json")
        
        if not research_json:
            self.add_error_to_state(state, "No research data available")
            raise ValueError("Missing research_json in state")
        
        try:
            scored_items = []
            total_tokens = 0
            
            # NOTEBOOK LOGIC: For each usecase-answer pair
            for item in research_json.items:
                usecase = item.usecase
                answer_text = item.answer
                
                self.logger.info(f"[SCORING] {usecase}...")
                
                # Score this use case (one LLM call)
                scores = self._score_usecase(
                    brand=prospect_name,
                    usecase=usecase,
                    answer_text=answer_text
                )
                
                # Calculate weighted final score (0-5 range)
                pain = scores["pain"]
                if pain == 0:
                    final_score = 0.0
                else:
                    final_score = (
                        self.W_COST * scores["cost_revenue"]
                        + self.W_BENCH * scores["benchmark_competition"]
                        + self.W_PRESS * scores["subjective_pressure"]
                        + self.W_PRIV * scores["privacy_relevance"]
                    )
                
                scored_items.append(UseCaseScore(
                    usecase=usecase,
                    pain=scores["pain"],
                    cost_revenue=scores["cost_revenue"],
                    benchmark_competition=scores["benchmark_competition"],
                    subjective_pressure=scores["subjective_pressure"],
                    privacy_relevance=scores["privacy_relevance"],
                    score=round(final_score, 3),
                    summary=scores["summary"]
                ))
                
                total_tokens += 200  # Approximate
            
            # Sort with tiebreaker logic (NEW: requested enhancement)
            scored_items_sorted = self._sort_with_tiebreaker(scored_items)
            
            # Build output (matches notebook format)
            output = AnalysisOutput(
                brand=prospect_name,
                generated_at=datetime.utcnow().isoformat(),
                weights={
                    "cost_revenue": self.W_COST,
                    "benchmark_competition": self.W_BENCH,
                    "subjective_pressure": self.W_PRESS,
                    "privacy_relevance": self.W_PRIV
                },
                items=scored_items_sorted
            )
            
            self.logger.info(f"Scored {len(scored_items_sorted)} use cases")
            self.logger.info(f"Top 3: {[item.usecase for item in scored_items_sorted[:3]]}")
            
            # Display table for human review (NEW: requested enhancement)
            self._display_scoring_table(scored_items_sorted)
            
            # Save to state (matches schema)
            state["analysis_json"] = output
            self.update_state_metadata(state, tokens=total_tokens)
            self.log_execution_end(success=True)
            
            return state
            
        except Exception as e:
            self.log_error(e)
            self.add_error_to_state(state, f"Analysis failed: {str(e)}")
            raise
    
    def _score_usecase(self, brand: str, usecase: str, answer_text: str) -> dict:
        """
        Score single use case using LLM.
        EXACT NOTEBOOK IMPLEMENTATION.
        
        Args:
            brand: Prospect name
            usecase: Use case slug
            answer_text: Tavily answer for this use case
            
        Returns:
            Dictionary with scores and summary
        """
        # Build prompt (exact notebook format)
        prompt = f"""{self.prompt}

Brand: {brand}
Use case: {usecase}

Evidence from web search (Tavily answer):
{answer_text}

Follow the instructions and output ONLY the JSON object.
"""
        
        # Call LLM
        response = self.llm.invoke(prompt)
        raw = response.content.strip()
        
        # Parse JSON (with notebook's fallback logic)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            # Try to extract JSON block (notebook logic)
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                raise ValueError(f"Could not parse JSON for {usecase}: {raw}")
            parsed = json.loads(match.group(0))
        
        # Validate and clamp values (notebook logic)
        pain = int(parsed.get("pain", 0))
        if pain not in (0, 1):
            pain = 0
        
        def clamp_int(v):
            try:
                v = int(v)
            except:
                v = 0
            return max(0, min(5, v))
        
        # Gating rule: if pain=0, all others must be 0
        if pain == 0:
            cost_revenue = 0
            benchmark_competition = 0
            subjective_pressure = 0
            privacy_relevance = 0
        else:
            cost_revenue = clamp_int(parsed.get("cost_revenue", 0))
            benchmark_competition = clamp_int(parsed.get("benchmark_competition", 0))
            subjective_pressure = clamp_int(parsed.get("subjective_pressure", 0))
            privacy_relevance = clamp_int(parsed.get("privacy_relevance", 0))
        
        summary = parsed.get("summary", "").strip()
        
        return {
            "pain": pain,
            "cost_revenue": cost_revenue,
            "benchmark_competition": benchmark_competition,
            "subjective_pressure": subjective_pressure,
            "privacy_relevance": privacy_relevance,
            "summary": summary
        }
    
    def _sort_with_tiebreaker(self, scored_items: list) -> list:
        """
        Sort by score descending, with tiebreaker logic.
        NEW: Enhanced sorting as requested.
        
        Tiebreaker order if scores are equal:
        1. cost_revenue (higher is better)
        2. benchmark_competition (higher is better)
        3. subjective_pressure (higher is better)
        4. privacy_relevance (higher is better)
        """
        return sorted(
            scored_items,
            key=lambda x: (
                x.score,                      # Primary: overall score
                x.cost_revenue,               # Tie 1: financial impact
                x.benchmark_competition,      # Tie 2: competitive gap
                x.subjective_pressure,        # Tie 3: urgency
                x.privacy_relevance           # Tie 4: compliance risk
            ),
            reverse=True
        )
    
    def _display_scoring_table(self, scored_items: list):
        """
        Display scoring table for human review.
        NEW: Requested enhancement for better UX.
        """
        print("\n" + "="*120)
        print("USE CASE SCORING RESULTS")
        print("="*120)
        print(f"{'#':<4} {'Use Case':<35} {'Pain':<6} {'Cost':<6} {'Bench':<6} {'Press':<6} {'Priv':<6} {'Score':<8}")
        print("-"*120)
        
        for i, item in enumerate(scored_items, 1):
            # Shorten usecase name for display
            usecase_short = item.usecase.replace("usecases__", "").replace("_", " ")[:33]
            
            print(
                f"{i:<4} {usecase_short:<35} "
                f"{item.pain:<6} "
                f"{item.cost_revenue:<6} "
                f"{item.benchmark_competition:<6} "
                f"{item.subjective_pressure:<6} "
                f"{item.privacy_relevance:<6} "
                f"{item.score:<8.2f}"
            )
        
        print("="*120)
        print(f"\nTop 3 Recommendations:")
        for i, item in enumerate(scored_items[:3], 1):
            usecase_display = item.usecase.replace("usecases__", "").replace("_", " ").title()
            print(f"  {i}. {usecase_display} (score: {item.score:.2f})")
            print(f"     {item.summary[:100]}...")
        
        print("\n" + "="*120 + "\n")