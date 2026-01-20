"""Checkpoint 2: Final Review with 3-way Routing UI."""

import streamlit as st
from src.state.schemas import WorkflowState, CheckpointAction
from pathlib import Path


def render_checkpoint_2(state: WorkflowState) -> dict:
    """
    Render Checkpoint 2 UI with 3-way routing options.
    
    Args:
        state: Current workflow state
        
    Returns:
        Dict with user's action
    """
    st.warning("⚠️ **Human Review Required: Final Presentation**")
    
    st.subheader("📊 Generated Presentation")
    
    # Get content and PPTX path
    content_json = state.get("content_json")
    pptx_path = state.get("pptx_path")
    
    if not content_json:
        st.error("No presentation content available")
        return None
    
    if not pptx_path:
        st.error("PPTX file not generated")
        return None
    
    # Show download button prominently
    st.markdown("### 📥 Download Presentation")
    
    try:
        with open(pptx_path, "rb") as file:
            pptx_data = file.read()
            st.download_button(
                label="⬇️ **Download PowerPoint**",
                data=pptx_data,
                file_name=Path(pptx_path).name,
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                type="primary",
                use_container_width=True
            )
    except Exception as e:
        st.error(f"Error loading PPTX: {e}")
    
    # Display slide preview
    st.markdown("---")
    st.subheader("👁️ Slide Preview")
    st.info(f"Generated {len(content_json.slides)} slides for {content_json.brand}")
    
    # Create tabs for slides
    slide_tabs = st.tabs([f"Slide {slide.slide}" for slide in content_json.slides])
    
    for i, slide in enumerate(content_json.slides):
        with slide_tabs[i]:
            st.markdown(f"### Slide {slide.slide}: {slide.title}")
            
            # Content
            if slide.content and slide.content != "STATIC_TEMPLATE":
                st.markdown("**Content:**")
                st.write(slide.content)
            
            # Bullets
            if slide.bullets:
                st.markdown("**Key Points:**")
                for bullet in slide.bullets:
                    st.write(f"• {bullet}")
            
            # Product info (for solution slides)
            if hasattr(slide, 'product') and slide.product:
                st.markdown(f"**Product:** {slide.product}")
            
            # Products list (for complementary slides)
            if hasattr(slide, 'products') and slide.products:
                st.markdown(f"**Products:** {', '.join(slide.products)}")
            
            # Brand value
            if hasattr(slide, 'value') and slide.value:
                st.markdown(f"**Value Proposition:** {slide.value}")
    
    # Show summary
    st.markdown("---")
    st.subheader("📋 Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Slides", len(content_json.slides))
    
    with col2:
        selected_usecases = state.get("top_3_usecases", [])
        st.metric("Use Cases", len(selected_usecases))
    
    with col3:
        product_mapping = state.get("product_mapping_json")
        if product_mapping and product_mapping.solutions:
            primary_count = sum(1 for sol in product_mapping.solutions if len(sol.products) > 0)
            st.metric("Solutions Mapped", primary_count)
        else:
            st.metric("Solutions Mapped", "N/A")
    
    # Decision time
    st.markdown("---")
    st.subheader("🎯 What would you like to do?")
    
    st.write("Choose one of the following options:")
    
    # Create columns for 4 buttons
    col1, col2, col3, col4 = st.columns(4)
    
    feedback = None
    
    with col1:
        if st.button("✅ **Approve & Finish**", type="primary", use_container_width=True):
            feedback = {"action": CheckpointAction.APPROVE}
            st.success("✨ Presentation approved!")
            st.balloons()
    
    with col2:
        with st.popover("🔄 Rechoose Use Cases"):
            st.write("**Go back to use case selection**")
            st.write("")
            st.write("This will:")
            st.write("• Return to Checkpoint 1")
            st.write("• Let you select different use cases")
            st.write("• Regenerate everything from there")
            st.write("")
            
            if st.button("Confirm: Rechoose Use Cases", key="confirm_rechoose", use_container_width=True):
                feedback = {"action": CheckpointAction.RECHOOSE_USECASES}
                st.info("Going back to use case selection...")
    
    with col3:
        with st.popover("🎯 Change Products"):
            st.write("**Remap products**")
            st.write("")
            st.write("This will:")
            st.write("• Keep current use cases")
            st.write("• Regenerate product mapping")
            st.write("• Regenerate content and slides")
            st.write("")
            
            if st.button("Confirm: Change Products", key="confirm_products", use_container_width=True):
                feedback = {"action": CheckpointAction.CHANGE_PRODUCTS}
                st.info("Remapping products...")
    
    with col4:
        with st.popover("✍️ Modify Content"):
            st.write("**Regenerate content**")
            st.write("")
            st.write("This will:")
            st.write("• Keep current use cases and products")
            st.write("• Regenerate slide content")
            st.write("• Create new PPTX")
            st.write("")
            
            if st.button("Confirm: Modify Content", key="confirm_content", use_container_width=True):
                feedback = {"action": CheckpointAction.MODIFY_CONTENT}
                st.info("Regenerating content...")
    
    return feedback