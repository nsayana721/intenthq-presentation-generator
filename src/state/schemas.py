from typing import TypedDict, List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class CheckpointAction(str, Enum):
    """Actions available at checkpoints."""
    APPROVE = "approve"
    RECHOOSE_USECASES = "rechoose_usecases"
    CHANGE_PRODUCTS = "change_products"
    MODIFY_CONTENT = "modify_content"


# ==================== AGENT 3: Query Generator Output ====================
class UseCaseQuery(BaseModel):
    """Single use case query pair (Agent 3 output)."""
    usecase: str  # e.g., "usecases__customer-acquisition"
    query: str    # Optimized Tavily search query


class QueryGeneratorOutput(BaseModel):
    """Complete output from Agent 3 (Query Generator)."""
    brand: str
    generated_at: str
    items: List[UseCaseQuery]


# ==================== AGENT 4: Tavily Research Output ====================
class UseCaseResearch(BaseModel):
    """Single use case research result (Agent 4 output)."""
    usecase: str
    answer: str  # Long-form Tavily answer


class TavilyResearchOutput(BaseModel):
    """Complete output from Agent 4 (Prospect Research)."""
    brand: str
    generated_at: str
    items: List[UseCaseResearch]


# ==================== AGENT 5: Analysis/Scoring Output ====================
class UseCaseScore(BaseModel):
    """Scored use case with pain analysis (Agent 5 output)."""
    usecase: str
    pain: int = Field(ge=0, le=1)  # Binary: 0 or 1
    cost_revenue: int = Field(ge=0, le=5)
    benchmark_competition: int = Field(ge=0, le=5)
    subjective_pressure: int = Field(ge=0, le=5)
    privacy_relevance: int = Field(ge=0, le=5)
    score: float = Field(ge=0, le=5)  # Weighted score
    summary: str


class AnalysisOutput(BaseModel):
    """Complete output from Agent 5 (Analysis)."""
    brand: str
    generated_at: str
    weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "cost_revenue": 0.4,
            "benchmark_competition": 0.3,
            "subjective_pressure": 0.2,
            "privacy_relevance": 0.1
        }
    )
    items: List[UseCaseScore]


# ==================== AGENT 6: Product Mapping Output ====================
class ProductSolution(BaseModel):
    """Single product recommendation."""
    name: str  # e.g., "platform__intent-lift"
    role: str  # Detailed description of how product solves use case


class UseCaseSolution(BaseModel):
    """Products mapped to a use case (Agent 6 output)."""
    usecase: str
    products: List[ProductSolution]
    brand_value: str  # Value proposition for the brand


class ProductMappingOutput(BaseModel):
    """Complete output from Agent 6 (Product Mapper)."""
    brand: str
    generated_at: str
    solutions: List[UseCaseSolution]


# ==================== AGENT 7: Content Creator Output ====================
class SlideContent(BaseModel):
    """Content for a single slide (Agent 7 output)."""
    slide: int  # Note: "slide" not "slide_number" to match notebook
    title: str
    content: Optional[str] = None
    bullets: Optional[List[str]] = None


class ContentCreatorOutput(BaseModel):
    """Complete output from Agent 7 (Content Creator)."""
    brand: str
    generated_at: str
    slides: List[SlideContent]


# ==================== WORKFLOW STATE (LangGraph State) ====================
class WorkflowState(TypedDict):
    """
    Complete state for the workflow.
    This flows through all agents via LangGraph.
    """
    # ==================== INPUT ====================
    prospect_name: str
    user_preferences: Dict[str, Any]
    execution_id: str
    
    # ==================== PHASE 1: INTENTHQ DATA (Cache: 14 days) ====================
   
    # Agent 1: Scraped markdown files
    intenthq_content_raw: Optional[Dict[str, Any]]  # Raw scrape data
    
    # Agent 2: Cleaned markdown files
    intenthq_content_cleaned: Optional[Dict[str, Any]]  # Cleaned content
    
    intenthq_cache_hit: bool
    
    # ==================== PHASE 2: PROSPECT INTELLIGENCE (Cache: 3 days) ====================
    # Agent 3: Query generation
    queries_json: Optional[QueryGeneratorOutput]
    
    # Agent 4: Tavily research
    research_json: Optional[TavilyResearchOutput]
    prospect_cache_hit: bool
    
    # ==================== HUMAN CHECKPOINT 1 ====================
    # Agent 5: Analysis & scoring
    analysis_json: Optional[AnalysisOutput]
    
    # Human selection
    top_3_usecases: Optional[List[str]]  # Selected use case names
    checkpoint1_approved: bool
    
    # ==================== PHASE 3: PRODUCT MAPPING ====================
    # Agent 6: Product recommendations
    product_mapping_json: Optional[ProductMappingOutput]
    
    # ==================== PHASE 4: CONTENT GENERATION ====================
    # Agent 7: Slide content
    content_json: Optional[ContentCreatorOutput]
    
    # Agent 8: PPTX file
    pptx_path: Optional[str]
    
    # ==================== HUMAN CHECKPOINT 2 ====================
    checkpoint2_action: Optional[CheckpointAction]
    human_feedback: Dict[str, Any]
    
    # ==================== WORKFLOW CONTROL ====================
    current_step: str
    needs_human_review: bool
    retry_count: int
    
    # ==================== METADATA ====================
    error_log: List[Dict[str, str]]
    created_at: datetime
    updated_at: datetime
    total_tokens_used: int
    execution_time_seconds: float


def create_initial_state(prospect_name: str, user_preferences: Dict[str, Any] = None) -> WorkflowState:
    """
    Create initial workflow state.
    
    Args:
        prospect_name: Name of the prospect company (e.g., "Barclays")
        user_preferences: Optional user configuration
        
    Returns:
        Initial WorkflowState
    """
    import uuid
    
    if user_preferences is None:
        user_preferences = {}
    
    return WorkflowState(
        # Input
        prospect_name=prospect_name,
        user_preferences=user_preferences,
        execution_id=str(uuid.uuid4()),
        
        # Phase 1: IntentHQ data
        intenthq_content_raw=None,
        intenthq_content_cleaned=None,
        intenthq_cache_hit=False,
        
        # Phase 2: Prospect intelligence
        queries_json=None,
        research_json=None,
        prospect_cache_hit=False,
        
        # Human Checkpoint 1
        analysis_json=None,
        top_3_usecases=None,
        checkpoint1_approved=False,
        
        # Phase 3: Product mapping
        product_mapping_json=None,
        
        # Phase 4: Content generation
        content_json=None,
        pptx_path=None,
        
        # Human Checkpoint 2
        checkpoint2_action=None,
        human_feedback={},
        
        # Workflow control
        current_step="initialized",
        needs_human_review=False,
        retry_count=0,
        
        # Metadata
        error_log=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
        total_tokens_used=0,
        execution_time_seconds=0.0
    )