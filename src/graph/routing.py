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
    # Default to continuing if not explicitly set to regenerate
    if state.get("checkpoint1_approved", True):  # Default True
        logger.info("Checkpoint 1: Approved, proceeding to product mapping")
        return "product_mapper"
    else:
        logger.info("Checkpoint 1: Regenerating analysis")
        return "analyst"


def route_after_checkpoint_2(state: WorkflowState) -> str:
    """
    Route after Checkpoint 2 (final review).
    
    3-way routing:
    1. Approve → END
    2. Rechoose use cases → Checkpoint 1
    3. Change products → Product Mapper
    4. Modify content → Content Creator
    
    Args:
        state: Current workflow state
        
    Returns:
        Name of next node
    """
    action = state.get("checkpoint2_action", CheckpointAction.APPROVE)
    
    logger.info(f"Checkpoint 2 action: {action}")
    
    if action == CheckpointAction.APPROVE:
        return "END"
    
    elif action == CheckpointAction.RECHOOSE_USECASES:
        logger.info("Restarting from use case selection")
        # Clear downstream state
        state["product_mapping_json"] = None
        state["content_json"] = None
        state["pptx_path"] = None
        return "checkpoint_1"
    
    elif action == CheckpointAction.CHANGE_PRODUCTS:
        logger.info("Restarting from product mapping")
        # Clear content and slides
        state["content_json"] = None
        state["pptx_path"] = None
        return "product_mapper"
    
    elif action == CheckpointAction.MODIFY_CONTENT:
        logger.info("Restarting from content generation")
        # Clear only slides
        state["pptx_path"] = None
        return "content_creator"
    
    else:
        logger.warning(f"Unknown action: {action}, ending workflow")
        return "END"


def should_show_checkpoint_1(state: WorkflowState) -> bool:
    """Always show checkpoint 1 for use case selection."""
    return True


def should_show_checkpoint_2(state: WorkflowState) -> bool:
    """Always show checkpoint 2 for final review."""
    return True