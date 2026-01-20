"""Progress tracking component."""

import streamlit as st
from src.state.schemas import WorkflowState


def render_progress_tracker(state: WorkflowState, next_node: str = None):
    """
    Render workflow progress tracker.
    
    Args:
        state: Current workflow state
        next_node: Next node to execute (from checkpoint)
    """
    st.subheader("📊 Workflow Progress")
    
    # Define workflow steps (in order)
    steps = [
        ("scraper", "1. Scraping IntentHQ"),
        ("cleaner", "2. Cleaning Content"),
        ("query_generator", "3. Generating Queries"),
        ("researcher", "4. Researching Prospect"),
        ("analyst", "5. Analyzing Use Cases"),
        ("checkpoint_1", "⏸️ Checkpoint 1: Select"),
        ("product_mapper", "6. Mapping Products"),
        ("content_creator", "7. Creating Content"),
        ("slide_maker", "8. Building Slides"),
        ("checkpoint_2", "⏸️ Checkpoint 2: Review"),
    ]
    
    # Determine current position
    if next_node:
        # Find position based on next_node
        try:
            current_idx = next(i for i, (step_key, _) in enumerate(steps) if step_key == next_node)
        except StopIteration:
            # Workflow complete
            current_idx = len(steps)
    else:
        # Workflow just started or completed
        # Check if any work has been done
        if state.get("analysis_json"):
            current_idx = len(steps)  # Complete
        else:
            current_idx = 0  # Not started yet
   
    
    # Calculate progress
    progress = min(1.0, (current_idx + 1) / len(steps))
    
    # Progress bar
    st.progress(progress)
    
    if current_idx < len(steps):
        status_msg = f"Current: {steps[current_idx][1]}"
        if next_node:
            status_msg += f" → Next: {next_node}"
        st.caption(status_msg)
    else:
        st.caption("✅ Workflow Complete!")
    
    # Step indicators in columns
    cols = st.columns(len(steps))
    for i, (step_key, step_name) in enumerate(steps):
        with cols[i]:
            if i < current_idx:
                st.success("✅")
            elif i == current_idx:
                if next_node == step_key:
                    st.warning("⏸️")  # Paused before this
                else:
                    st.info("▶️")  # Currently running
            else:
                st.text("⏳")
            
            # Abbreviated label
            short_name = step_name.split(". ")[-1].replace("Checkpoint ", "CP")
            st.caption(short_name[:12])
    
    # Cache status
    st.markdown("---")
    st.subheader("💾 Cache Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        intenthq_cached = state.get("intenthq_cache_hit", False)
        if intenthq_cached:
            st.success("✅ IntentHQ Data (Cached)")
        else:
            st.info("🔄 IntentHQ Data (Fresh)")
    
    with col2:
        prospect_cached = state.get("prospect_cache_hit", False)
        if prospect_cached:
            st.success("✅ Prospect Data (Cached)")
        else:
            st.info("🔄 Prospect Data (Fresh)")
    
    # Metadata
    with st.expander("📈 Execution Details"):
        col1, col2 = st.columns(2)
        
        with col1:
            exec_id = state.get("execution_id", "N/A")
            st.text(f"ID: {exec_id[:12]}...")
            
            tokens = state.get("total_tokens_used", 0)
            st.text(f"Tokens: {tokens:,}")
        
        with col2:
            created = state.get("created_at")
            if created:
                # created_at is datetime object, not string
                if isinstance(created, str):
                    st.text(f"Started: {created[:19]}")
                else:
                    st.text(f"Started: {created.strftime('%Y-%m-%d %H:%M')}")
            
            errors = len(state.get("error_log", []))
            if errors > 0:
                st.error(f"Errors: {errors}")
            else:
                st.success("Errors: 0")