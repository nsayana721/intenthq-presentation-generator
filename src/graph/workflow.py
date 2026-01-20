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
    route_after_checkpoint_2,
    route_after_research
)
import logging


class WorkflowOrchestrator:
    """
    Main workflow orchestrator using LangGraph.
    
    Flow:
    1. Scrape → Clean → Query Gen → Research
    2. Analysis → [Checkpoint 1: Select Use Cases]
    3. Product Mapping → Content Generation → Slide Making
    4. [Checkpoint 2: Review (3-way routing)]
    5. End or Loop back based on user choice
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
        
        # Compile graph
        self.compiled_graph = self.graph.compile(checkpointer=self.checkpointer)
        self.logger.info("Workflow initialized successfully")
    
    def _build_workflow(self):
        """Build the LangGraph workflow."""
        
        # ==================== ADD NODES ====================
        
        # Phase 1-2: Data Collection & Research
        self.graph.add_node("scraper", self.scraper)
        self.graph.add_node("cleaner", self.cleaner)
        self.graph.add_node("query_generator", self.query_generator)
        self.graph.add_node("researcher", self.researcher)
        
        # Phase 3: Analysis
        self.graph.add_node("analysis_agent", self.analyst)
        
        # Human Checkpoint 1
        self.graph.add_node("checkpoint_1", self._checkpoint_1)
        
        # Phase 4-6: Mapping, Content, Slides
        self.graph.add_node("product_mapper", self.product_mapper)
        self.graph.add_node("content_creator", self.content_creator)
        self.graph.add_node("slide_maker", self.slide_maker)
        
        # Human Checkpoint 2
        self.graph.add_node("checkpoint_2", self._checkpoint_2)
        
        # ==================== DEFINE FLOW ====================
        
        # Set entry point
        self.graph.set_entry_point("scraper")
        
        # Phase 1-2: Linear flow
        self.graph.add_edge("scraper", "cleaner")
        self.graph.add_edge("cleaner", "query_generator")
        self.graph.add_edge("query_generator", "researcher")
        
        # After research: conditional routing
        self.graph.add_conditional_edges(
            "researcher",
            route_after_research,
            {
                "analysis_agent": "analysis_agent",
                "research_agent": "researcher"  # Retry if needed
            }
        )
        
        # Analysis → Checkpoint 1
        self.graph.add_edge("analysis_agent", "checkpoint_1")
        
        # After Checkpoint 1: conditional routing
        self.graph.add_conditional_edges(
            "checkpoint_1",
            route_after_checkpoint_1,
            {
                "product_mapper": "product_mapper",
                "analysis_agent": "analysis_agent"  # Regenerate if requested
            }
        )
        
        # Product Mapping → Content → Slides
        self.graph.add_edge("product_mapper", "content_creator")
        self.graph.add_edge("content_creator", "slide_maker")
        self.graph.add_edge("slide_maker", "checkpoint_2")
        
        # After Checkpoint 2: 3-way routing
        self.graph.add_conditional_edges(
            "checkpoint_2",
            route_after_checkpoint_2,
            {
                "END": END,
                "checkpoint_1": "checkpoint_1",  # Rechoose use cases
                "product_mapper": "product_mapper",  # Change products
                "content_creator": "content_creator"  # Modify content
            }
        )
        
        self.logger.info("Workflow graph built successfully")
    
    def _checkpoint_1(self, state: WorkflowState) -> WorkflowState:
        """
        Human Checkpoint 1: Use case selection.
        Pauses execution for user to select use cases.
        """
        self.logger.info("Reached Checkpoint 1: Use case selection")
        state["current_step"] = "checkpoint_1"
        state["needs_human_review"] = True
        return state
    
    def _checkpoint_2(self, state: WorkflowState) -> WorkflowState:
        """
        Human Checkpoint 2: Final review with 3-way choice.
        Pauses execution for user to review slides and choose action.
        """
        self.logger.info("Reached Checkpoint 2: Final review")
        state["current_step"] = "checkpoint_2"
        state["needs_human_review"] = True
        return state
    
    def run(self, initial_state: WorkflowState, thread_id: str = None):
        """
        Start workflow execution.
        
        Args:
            initial_state: Initial workflow state
            thread_id: Thread ID for checkpoint persistence (defaults to execution_id)
            
        Returns:
            Final state after execution
        """
        thread_id = thread_id or initial_state["execution_id"]
        config = {"configurable": {"thread_id": thread_id}}
        
        self.logger.info(f"Starting workflow for {initial_state['prospect_name']}")
        
        try:
            # Execute workflow
            final_state = self.compiled_graph.invoke(initial_state, config)
            
            self.logger.info("Workflow execution complete")
            return final_state
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}", exc_info=True)
            raise
    
    def resume(self, state: WorkflowState, thread_id: str):
        """
        Resume workflow after human checkpoint.
        
        Args:
            state: Current state with human feedback
            thread_id: Thread ID to resume
            
        Returns:
            Updated state after resuming
        """
        config = {"configurable": {"thread_id": thread_id}}
        
        # Clear needs_human_review flag
        state["needs_human_review"] = False
        
        self.logger.info(f"Resuming workflow from {state['current_step']}")
        
        try:
            # Continue execution
            updated_state = self.compiled_graph.invoke(state, config)
            
            return updated_state
            
        except Exception as e:
            self.logger.error(f"Workflow resume failed: {e}", exc_info=True)
            raise
    
    def get_graph_visualization(self) -> str:
        """
        Get Mermaid visualization of the workflow graph.
        
        Returns:
            Mermaid diagram string
        """
        try:
            return self.compiled_graph.get_graph().draw_mermaid()
        except:
            return "Graph visualization not available"