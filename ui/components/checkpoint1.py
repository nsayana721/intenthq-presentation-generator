"""Checkpoint 1: Use Case Selection UI."""

import streamlit as st
from src.state.schemas import WorkflowState


def render_checkpoint_1(state: WorkflowState, orchestrator) -> dict:
    """
    Render Checkpoint 1 UI for use case selection.
    
    Args:
        state: Current workflow state
        orchestrator: WorkflowOrchestrator instance (to check next_node)
        
    Returns:
        Dict with user's selections
    """
    st.warning("⚠️ **Human Review Required: Use Case Selection**")
    
    # Get analysis results
    analysis_json = state.get("analysis_json")
    if not analysis_json:
        st.error("No analysis data available")
        return None
    
    # Show prospect info
    st.subheader(f"📊 Analysis for {analysis_json.brand}")
    st.info(f"Analyzed {len(analysis_json.items)} use cases. Here are the results:")
    
    # Display scoring table
    st.subheader("🎯 Use Case Scores")
    
    table_data = []
    for i, item in enumerate(analysis_json.items, 1):
        table_data.append({
            "#": i,
            "Use Case": item.usecase.replace("use-cases__", "").replace("-", " ").title(),
            "Pain": "✅" if item.pain == 1 else "❌",
            "Cost": item.cost_revenue,
            "Benchmark": item.benchmark_competition,
            "Pressure": item.subjective_pressure,
            "Privacy": item.privacy_relevance,
            "Score": f"{item.score:.2f}"
        })
    
    st.dataframe(table_data, use_container_width=True, hide_index=True)
    
    # Show top 3 AI recommendations
    st.markdown("---")
    st.subheader("🏆 Top 3 AI Recommendations")
    
    top_3 = analysis_json.items[:3]
    
    for i, item in enumerate(top_3, 1):
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### {i}. {item.usecase.replace('use-cases__', '').replace('-', ' ').title()}")
                st.write(item.summary)
            
            with col2:
                st.metric("Score", f"{item.score:.2f}")
            
            with st.expander("💡 Details"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Cost Impact", item.cost_revenue)
                with col2:
                    st.metric("Benchmark", item.benchmark_competition)
                with col3:
                    st.metric("Pressure", item.subjective_pressure)
                with col4:
                    st.metric("Privacy", item.privacy_relevance)
            
            st.divider()
    
    # Selection mode
    st.markdown("---")
    st.subheader("📋 Your Choice")
    
    selection_mode = st.radio(
        "How would you like to proceed?",
        ["✅ Accept AI's top 3 recommendations", "🔧 Choose my own 3 use cases"],
        key="selection_mode"
    )
    
    selected_use_cases = []
    
    if selection_mode == "✅ Accept AI's top 3 recommendations":
        # Use AI's top 3
        selected_use_cases = [item.usecase for item in top_3]
        
        st.success("✅ Using AI's recommended use cases:")
        for i, uc in enumerate(top_3, 1):
            st.write(f"{i}. {uc.usecase.replace('use-cases__', '').replace('-', ' ').title()}")
    
    else:
        # Manual selection
        st.write("Select exactly 3 use cases from the full list:")
        
        # Show all use cases with checkboxes
        selections = []
        for item in analysis_json.items:
            display_name = item.usecase.replace("use-cases__", "").replace("-", " ").title()
            if st.checkbox(
                f"{display_name} (Score: {item.score:.2f})",
                key=f"uc_{item.usecase}"
            ):
                selections.append(item.usecase)
        
        if len(selections) != 3:
            st.warning(f"⚠️ Please select exactly 3 use cases (currently: {len(selections)})")
        else:
            selected_use_cases = selections
            st.success(f"✅ 3 use cases selected")
    
    # Action buttons
    st.markdown("---")
    st.subheader("🚀 What's Next?")
    
    col1, col2 = st.columns(2)
    
    feedback = None
    
    with col1:
        if st.button(
            "✅ **Approve & Continue**", 
            type="primary", 
            disabled=len(selected_use_cases) != 3,
            use_container_width=True
        ):
            feedback = {
                "top_3_usecases": selected_use_cases,
                "approved": True
            }
            st.success("Continuing to product mapping...")
    
    with col2:
        if st.button("🔄 **Regenerate Analysis**", use_container_width=True):
            feedback = {
                "top_3_usecases": [],
                "approved": False
            }
            st.info("Regenerating analysis...")
    
    return feedback