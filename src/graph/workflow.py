"""
Main LangGraph workflow orchestrator.
Defines the complete agent workflow with conditional routing.
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from src.state.schemas import WorkflowState
from src.agents.scraper_agent import ScraperAgent
from src.agents.cleaner_agent import CleanerAgent
from src.agents.query_generator_agent import QueryGeneratorAgent
from src.agents.research_agent import ResearchAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.product_mapper_agent import ProductMapperAgent
from src.agents.content_creator_agent import ContentCreatorAgent
from src.agents.slide_maker_agent import SlideMakerAgent
from src.graph.routing import (
    route_after_checkpoint_1,
    route_after_checkpoint_2
)
import logging


class WorkflowOrchestrator:
    """
    Main workflow orchestrator using LangGraph.
    
    Flow:
    Phase 1: Data Collection (14-day cache)
      1. Scraper → Cleaner
    
    Phase 2: Prospect Intelligence (3-day cache per client)
      2. Query Generator → Research
    
    Checkpoint 1: Use Case Selection
      3. Analysis → [Human selects top 3]
    
    Phase 3-4: Solution Generation
      4. Product Mapper → Content Creator → Slide Maker
    
    Checkpoint 2: Final Review (3-way routing)
      5. [Human: Approve / Rechoose / Change / Modify]
    """
    
    def __init__(self):
        self.logger = logging.getLogger("workflow")
        
        # Initialize all agents
        self.logger.info("Initializing agents...")
        self.scraper = ScraperAgent()
        self.cleaner = CleanerAgent()
        self.query_generator = QueryGeneratorAgent()
        self.researcher = ResearchAgent()
        self.analyst = AnalysisAgent()
        self.product_mapper = ProductMapperAgent()
        self.content_creator = ContentCreatorAgent()
        self.slide_maker = SlideMakerAgent()
        
        # Initialize graph
        self.graph = StateGraph(WorkflowState)
        self.checkpointer = MemorySaver()
        
        # Build the workflow
        self._build_workflow()
        
        # Compile graph with interrupts AFTER key agents
        self.compiled_graph = self.graph.compile(
            checkpointer=self.checkpointer,
            interrupt_after=["analyst", "slide_maker"]  # Pause after these agents
        )
        self.logger.info("Workflow initialized successfully")
    
    def _build_workflow(self):
        """Build the LangGraph workflow."""
        
        # ==================== ADD NODES ====================
        
        # Phase 1: IntentHQ data (14-day cache)
        self.graph.add_node("scraper", self.scraper)
        self.graph.add_node("cleaner", self.cleaner)
        
        # Phase 2: Prospect research (3-day cache)
        self.graph.add_node("query_generator", self.query_generator)
        self.graph.add_node("researcher", self.researcher)
        
        # Phase 3: Analysis
        self.graph.add_node("analyst", self.analyst)
        
        # Checkpoint 1
        self.graph.add_node("checkpoint_1", self._checkpoint_1)
        
        # Phase 4-6: Solution pipeline
        self.graph.add_node("product_mapper", self.product_mapper)
        self.graph.add_node("content_creator", self.content_creator)
        self.graph.add_node("slide_maker", self.slide_maker)
        
        # Checkpoint 2
        self.graph.add_node("checkpoint_2", self._checkpoint_2)
        
        # ==================== DEFINE EDGES ====================
        
        # Entry point
        self.graph.set_entry_point("scraper")
        
        # Phase 1: Data collection (linear, cached)
        self.graph.add_edge("scraper", "cleaner")
        self.graph.add_edge("cleaner", "query_generator")
        
        # Phase 2: Research (linear, cached per client)
        self.graph.add_edge("query_generator", "researcher")
        self.graph.add_edge("researcher", "analyst")
        
        # Checkpoint 1 (conditional)
        self.graph.add_edge("analyst", "checkpoint_1")
        self.graph.add_conditional_edges(
            "checkpoint_1",
            route_after_checkpoint_1,
            {
                "product_mapper": "product_mapper",
                "analyst": "analyst"  # Regenerate if needed
            }
        )
        
        # Phase 4-6: Solution pipeline (linear)
        self.graph.add_edge("product_mapper", "content_creator")
        self.graph.add_edge("content_creator", "slide_maker")
        self.graph.add_edge("slide_maker", "checkpoint_2")
        
        # Checkpoint 2 (3-way routing)
        self.graph.add_conditional_edges(
            "checkpoint_2",
            route_after_checkpoint_2,
            {
                "END": END,
                "checkpoint_1": "checkpoint_1",
                "product_mapper": "product_mapper",
                "content_creator": "content_creator"
            }
        )
        
        self.logger.info("Workflow graph built successfully")
    
    
    def _checkpoint_1(self, state: WorkflowState) -> WorkflowState:
        """Checkpoint 1: Route based on user selections (runs after pause)."""
        self.logger.info("=== CHECKPOINT 1: Routing based on user selections ===")
        return state
    
    def _checkpoint_2(self, state: WorkflowState) -> WorkflowState:
        """Checkpoint 2: Route based on user action (runs after pause)."""
        self.logger.info("=== CHECKPOINT 2: Routing based on user action ===")
        return state
    
    def run(self, initial_state: WorkflowState, thread_id: str = None):
        """
        Start workflow execution.
        Runs until first checkpoint (interrupt_before), then pauses.
        
        Args:
            initial_state: Initial workflow state
            thread_id: Thread ID for persistence
            
        Returns:
            State at checkpoint
        """
        thread_id = thread_id or initial_state["execution_id"]
        config = {"configurable": {"thread_id": thread_id}}
        
        self.logger.info(f"Starting workflow for {initial_state['prospect_name']}")
        self.logger.info(f"Thread ID: {thread_id}")
        
        try:
            # Execute until first interrupt (after analyst)
            for _ in self.compiled_graph.stream(initial_state, config):
                pass  # Stream until paused
            
            # Get state at interrupt
            final_state = self.compiled_graph.get_state(config)
            state_values = final_state.values
            next_node = final_state.next[0] if final_state.next else "END"
            
            self.logger.info(f"Paused after agent, next node: {next_node}")
            
            # Should be paused with checkpoint_1 next
            if next_node != "checkpoint_1":
                raise RuntimeError(f"Expected checkpoint_1 next, got {next_node}")
            
            return state_values
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}", exc_info=True)
            raise
    
    def resume(self, user_input: dict, thread_id: str):
        """
        Resume workflow after human input at checkpoint.
        
        Args:
            user_input: Dict with user choices
                For Checkpoint 1: {"top_3_usecases": [...], "approved": True}
                For Checkpoint 2: {"action": "approve"}
            thread_id: Thread ID to resume
            
        Returns:
            Updated state (may pause again at next checkpoint)
        """
        config = {"configurable": {"thread_id": thread_id}}
        
        # Get current state
        checkpoint_state = self.compiled_graph.get_state(config)
        if not checkpoint_state:
            raise ValueError(f"No checkpoint found for thread {thread_id}")
        
        next_node = checkpoint_state.next[0] if checkpoint_state.next else "END"
        self.logger.info(f"Resuming, next node is: {next_node}")
        
        # Prepare state updates based on which checkpoint
        updates = {}
        
        if next_node == "checkpoint_1":
            # Paused after analyst, user selecting use cases
            updates["top_3_usecases"] = user_input.get("top_3_usecases", [])
            updates["checkpoint1_approved"] = user_input.get("approved", True)
            self.logger.info(f"User selected: {updates['top_3_usecases']}")
        
        elif next_node == "checkpoint_2":
            # Paused after slide_maker, user reviewing PPTX
            updates["checkpoint2_action"] = user_input.get("action", "approve")
            self.logger.info(f"User action: {updates['checkpoint2_action']}")
        
        else:
            raise ValueError(f"Cannot resume, next node is {next_node}")
        
        try:
            # Update state
            self.compiled_graph.update_state(config, updates)
            
            # Continue execution
            for _ in self.compiled_graph.stream(None, config):
                pass  # Stream until next pause or end
            
            # Get final state
            final_state = self.compiled_graph.get_state(config)
            state_values = final_state.values
            next_node = final_state.next[0] if final_state.next else None
            
            
            if next_node == "checkpoint_2":
                self.logger.info("Paused after slide_maker, awaiting final review")
            elif next_node is None:
                self.logger.info("Workflow complete")
            else:
                self.logger.info(f"Paused with next node: {next_node}")
            
            return state_values
            
        except Exception as e:
            self.logger.error(f"Workflow resume failed: {e}", exc_info=True)
            raise
    
    def get_graph_visualization(self) -> str:
        """Get Mermaid diagram of workflow."""
        try:
            return self.compiled_graph.get_graph().draw_mermaid()
        except:
            return "Graph visualization not available"