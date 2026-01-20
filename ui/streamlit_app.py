"""
Main Streamlit application for IntentHQ Presentation Generator.
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.graph.workflow import WorkflowOrchestrator
from src.state.schemas import create_initial_state, CheckpointAction
from src.utils.logger import setup_logging
from ui.components.progress_tracker import render_progress_tracker
from ui.components.checkpoint1 import render_checkpoint_1
from ui.components.checkpoint2 import render_checkpoint_2

# Setup logging
setup_logging()

# Page config
st.set_page_config(
    page_title="IntentHQ Presentation Generator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .stButton>button {
        width: 100%;
    }
    .checkpoint-banner {
        padding: 1rem;
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state."""
    if "workflow" not in st.session_state:
        st.session_state.workflow = None
    if "state" not in st.session_state:
        st.session_state.state = None
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None
    if "workflow_started" not in st.session_state:
        st.session_state.workflow_started = False


def get_next_node(workflow, thread_id):
    """Get the next node from checkpoint."""
    try:
        config = {"configurable": {"thread_id": thread_id}}
        checkpoint = workflow.compiled_graph.get_state(config)
        return checkpoint.next[0] if checkpoint.next else None
    except:
        return None


def main():
    """Main application."""
    initialize_session_state()
    
    # Header
    st.markdown('<p class="main-header">🎯 IntentHQ Presentation Generator</p>', unsafe_allow_html=True)
    st.markdown("*Autonomous AI agents create tailored sales presentations*")
    st.divider()
    
    # Sidebar - Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        prospect_name = st.text_input(
            "Prospect Company Name *",
            placeholder="e.g., Nike, Barclays, Spotify",
            help="Name of the company you're creating a presentation for",
            disabled=st.session_state.workflow_started
        )
        
        st.divider()
        
        # Start button
        if not st.session_state.workflow_started:
            if st.button("🚀 **Generate Presentation**", type="primary", disabled=not prospect_name):
                with st.spinner("Initializing workflow..."):
                    try:
                        # Initialize workflow
                        st.session_state.workflow = WorkflowOrchestrator()
                        
                        # Create initial state
                        initial_state = create_initial_state(
                            prospect_name=prospect_name,
                            user_preferences={}
                        )
                        
                        st.session_state.state = initial_state
                        st.session_state.thread_id = initial_state["execution_id"]
                        st.session_state.workflow_started = True
                        
                        st.success("Workflow initialized!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Initialization failed: {e}")
        
        # Clear button
        if st.session_state.workflow_started:
            st.markdown("---")
            if st.button("🗑️ Clear & Start Over", type="secondary"):
                st.session_state.workflow = None
                st.session_state.state = None
                st.session_state.thread_id = None
                st.session_state.workflow_started = False
                st.rerun()
    
    # Main content area
    if not st.session_state.workflow_started:
        # Landing page
        st.info("👈 Enter a prospect company name in the sidebar to begin")
        
        st.subheader("How it works:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Phase 1-2: Intelligence Gathering**
            1. 🌐 Scrape IntentHQ website (cached 14 days)
            2. 📚 Clean and structure content
            3. 🔍 Research prospect company (cached 3 days)
            4. 📊 Analyze use case fit with scoring
            """)
        
        with col2:
            st.markdown("""
            **Phase 3-4: Presentation Generation**
            5. ⏸️ **Checkpoint 1**: Select top 3 use cases
            6. 🎯 Map Intent HQ products to needs
            7. ✍️ Generate presentation content
            8. 🎨 Build PowerPoint slides
            9. ⏸️ **Checkpoint 2**: Review & finalize
            """)
        
        st.markdown("---")
        st.subheader("✨ Features")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🤖 8 AI Agents**")
            st.write("Specialized agents with reasoning")
        
        with col2:
            st.markdown("**⏸️ 2 Checkpoints**")
            st.write("Human-in-the-loop validation")
        
        with col3:
            st.markdown("**💾 Smart Caching**")
            st.write("14-day IntentHQ, 3-day client")
    
    else:
        # Workflow is running
        workflow = st.session_state.workflow
        state = st.session_state.state
        thread_id = st.session_state.thread_id
        
        # Get next node
        next_node = get_next_node(workflow, thread_id)
        
        # Progress tracker
        render_progress_tracker(state, next_node)
        
        st.divider()
        
        # Check if at checkpoint
        if next_node in ["checkpoint_1", "checkpoint_2"]:
            # At a checkpoint - show UI
            
            if next_node == "checkpoint_1":
                # Checkpoint 1: Use case selection
                st.markdown('<div class="checkpoint-banner">⏸️ <b>Workflow Paused</b> – Awaiting your input at Checkpoint 1</div>', unsafe_allow_html=True)
                
                feedback = render_checkpoint_1(state, workflow)
                
                if feedback:
                    with st.spinner("Resuming workflow..."):
                        try:
                            # Resume with user selections
                            updated_state = workflow.resume(feedback, thread_id)
                            st.session_state.state = updated_state
                            st.success("Resuming from Checkpoint 1...")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Resume failed: {e}")
            
            elif next_node == "checkpoint_2":
                # Checkpoint 2: Final review
                st.markdown('<div class="checkpoint-banner">⏸️ <b>Workflow Paused</b> – Awaiting your decision at Checkpoint 2</div>', unsafe_allow_html=True)
                
                feedback = render_checkpoint_2(state)
                
                if feedback:
                    action = feedback.get("action")
                    
                    if action == CheckpointAction.APPROVE:
                        # Workflow complete!
                        st.success("✅ Presentation Approved!")
                        st.balloons()
                        
                        # Show final download
                        pptx_path = state.get("pptx_path")
                        if pptx_path:
                            st.markdown("### 🎉 Your Presentation is Ready!")
                            
                            try:
                                with open(pptx_path, "rb") as file:
                                    st.download_button(
                                        label="📥 **Download Final Presentation**",
                                        data=file,
                                        file_name=Path(pptx_path).name,
                                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                        type="primary",
                                        use_container_width=True
                                    )
                            except Exception as e:
                                st.error(f"Error loading PPTX: {e}")
                            
                            # Show metadata
                            with st.expander("📈 Execution Metadata"):
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    tokens = state.get("total_tokens_used", 0)
                                    st.metric("Total Tokens", f"{tokens:,}")
                                
                                with col2:
                                    intenthq_hit = state.get("intenthq_cache_hit", False)
                                    prospect_hit = state.get("prospect_cache_hit", False)
                                    cache_hits = sum([intenthq_hit, prospect_hit])
                                    st.metric("Cache Hits", f"{cache_hits}/2")
                                
                                with col3:
                                    exec_id = state.get("execution_id", "N/A")
                                    st.metric("Execution ID", exec_id[:12] + "...")
                    
                    else:
                        # Looping back
                        with st.spinner("Processing your request..."):
                            try:
                                updated_state = workflow.resume(feedback, thread_id)
                                st.session_state.state = updated_state
                                st.info(f"Restarting from {action}...")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Resume failed: {e}")
        
        elif next_node is None:
            # Workflow complete (shouldn't reach here normally)
            st.success("✅ Workflow Complete!")
            
            pptx_path = state.get("pptx_path")
            if pptx_path:
                try:
                    with open(pptx_path, "rb") as file:
                        st.download_button(
                            label="📥 Download Presentation",
                            data=file,
                            file_name=Path(pptx_path).name,
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                        )
                except Exception as e:
                    st.error(f"Error: {e}")
        
        else:
            # Workflow is running - trigger execution
            st.info("⚙️ Agents are working... Please wait.")
            
            # Live log viewer
            log_container = st.empty()
            
            with st.spinner(f"Executing workflow..."):
                try:
                    if next_node:
                        st.warning("Unexpected state - workflow may be paused")
                    else:
                        # Stream execution with live updates
                        with st.status("Running agents...", expanded=True) as status:
                            for i, chunk in enumerate(workflow.compiled_graph.stream(state, {"configurable": {"thread_id": thread_id}})):
                                # Show which node just executed
                                if chunk:
                                    node_name = list(chunk.keys())[0] if chunk else "unknown"
                                    status.write(f"✅ Completed: {node_name}")
                            
                            status.update(label="Paused at checkpoint", state="complete")
                        
                        # Get updated state
                        updated_state = workflow.compiled_graph.get_state({"configurable": {"thread_id": thread_id}}).values
                        st.session_state.state = updated_state
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Workflow Error: {str(e)}")
                    
                    # Show error details
                    with st.expander("🐛 Error Details"):
                        st.code(str(e))
                        
                        if state.get("error_log"):
                            st.write("**Error Log:**")
                            for error in state["error_log"]:
                                st.write(f"- {error}")
        
        # Log viewer (always show)
        if st.session_state.workflow_started:
            with st.expander("📋 View Live Logs"):
                from datetime import datetime
                from pathlib import Path
                
                log_file = Path("logs") / f"app_{datetime.now().strftime('%Y%m%d')}.log"
                
                if log_file.exists():
                    try:
                        with open(log_file, "r") as f:
                            logs = f.readlines()
                            # Show last 50 lines
                            st.code("".join(logs[-50:]))
                    except:
                        st.warning("Could not read log file")
                else:
                    st.warning(f"Log file not found: {log_file}")


if __name__ == "__main__":
    main()