"""State management for workflow."""

from src.state.schemas import (
    # Workflow state
    WorkflowState,
    create_initial_state,
    
    # Agent outputs (matching notebook JSON)
    QueryGeneratorOutput,
    UseCaseQuery,
    TavilyResearchOutput,
    UseCaseResearch,
    AnalysisOutput,
    UseCaseScore,
    ProductMappingOutput,
    UseCaseSolution,
    ProductSolution,
    ContentCreatorOutput,
    SlideContent,
    
    # Enums
    CheckpointAction,
)

__all__ = [
    "WorkflowState",
    "create_initial_state",
    "QueryGeneratorOutput",
    "UseCaseQuery",
    "TavilyResearchOutput",
    "UseCaseResearch",
    "AnalysisOutput",
    "UseCaseScore",
    "ProductMappingOutput",
    "UseCaseSolution",
    "ProductSolution",
    "ContentCreatorOutput",
    "SlideContent",
    "CheckpointAction",
]