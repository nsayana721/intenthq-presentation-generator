"""
Routing logic for LangGraph conditional edges.
Determines next node based on state.
"""

from src.state.schemas import WorkflowState, CheckpointAction
import logging

logger = logging.getLogger("routing")


def route_after_checkpoint_1(state: WorkflowState) -> str:
    """
    Route after Checkpoint 1 (use case selection).
    
    Args:
        state: Current workflow state
        
    Returns:
        Name of next node
    """
    feedback = state.get("human_feedback", {})
    action = feedback.get("action", "approved")
    
    logger.info(f"Checkpoint 1 action: {action}")
    
    if action == "approved":
        # User approved selection, continue to product mapping
        return "product_mapper"
    elif action == "regenerate":
        # User wants to regenerate analysis
        return "analysis_agent"
    else:
        # Default: continue
        return "product_mapper"


def route_after_checkpoint_2(state: WorkflowState) -> str:
    """
    Route after Checkpoint 2 (final review).
    
    This is the 3-way routing based on user choice:
    1. Approve → Download (END)
    2. Rechoose use cases → Back to Checkpoint 1
    3. Change products → Back to Product Mapper
    4. Modify content → Back to Content Creator
    
    Args:
        state: Current workflow state
        
    Returns:
        Name of next node
    """
    feedback = state.get("human_feedback", {})
    action = feedback.get("action", CheckpointAction.APPROVE)
    
    logger.info(f"Checkpoint 2 action: {action}")
    
    if action == CheckpointAction.APPROVE:
        # User approved, workflow complete
        return "END"
    
    elif action == CheckpointAction.RECHOOSE_USECASES:
        # Go back to checkpoint 1 (analysis results)
        logger.info("Restarting from use case selection")
        
        # Clear downstream state
        state["product_mapping"] = None
        state["slide_content"] = None
        state["pptx_path"] = None
        
        return "checkpoint_1"
    
    elif action == CheckpointAction.CHANGE_PRODUCTS:
        # Go back to product mapping
        logger.info("Restarting from product mapping")
        
        # Clear content and slides
        state["slide_content"] = None
        state["pptx_path"] = None
        
        return "product_mapper"
    
    elif action == CheckpointAction.MODIFY_CONTENT:
        # Go back to content generation
        logger.info("Restarting from content generation")
        
        # Clear only slides
        state["pptx_path"] = None
        
        return "content_creator"
    
    else:
        # Default: end workflow
        logger.warning(f"Unknown action: {action}, ending workflow")
        return "END"


def route_after_research(state: WorkflowState) -> str:
    """
    Route after research phase.
    Check if research confidence is sufficient.
    
    Args:
        state: Current workflow state
        
    Returns:
        Name of next node
    """
    prospect_research = state.get("prospect_research")
    
    if not prospect_research:
        logger.error("No prospect research data")
        return "research_agent"  # Retry
    
    confidence = prospect_research.confidence_score
    logger.info(f"Research confidence: {confidence}")
    
    if confidence < 0.7:
        # Low confidence, flag for human review
        logger.warning("Low confidence, flagging for review")
        state["needs_human_review"] = True
    
    # Always continue to analysis (human can review at checkpoint 1)
    return "analysis_agent"


def should_show_checkpoint_1(state: WorkflowState) -> bool:
    """
    Determine if Checkpoint 1 should be shown.
    
    Args:
        state: Current workflow state
        
    Returns:
        True if checkpoint should be shown
    """
    # Always show checkpoint 1 (required for use case selection)
    return True


def should_show_checkpoint_2(state: WorkflowState) -> bool:
    """
    Determine if Checkpoint 2 should be shown.
    
    Args:
        state: Current workflow state
        
    Returns:
        True if checkpoint should be shown
    """
    # Always show checkpoint 2 (required for final review)
    return True