#!/usr/bin/env python3
"""
Complete Workflow Test (Agents 1-8 + LangGraph)
Tests full pipeline with simulated human checkpoints.
"""

import sys
sys.path.insert(0, '/home/claude/intenthq-presentation-generator')

from src.state.schemas import create_initial_state, CheckpointAction
from src.graph.workflow import WorkflowOrchestrator
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("="*80)
print("FULL WORKFLOW TEST")
print("="*80)

# ============================================================================
# STEP 1: Initialize Workflow
# ============================================================================
print("\n[STEP 1] Initializing workflow orchestrator...")
try:
    orchestrator = WorkflowOrchestrator()
    print("✅ Workflow initialized")
except Exception as e:
    print(f"❌ Initialization failed: {e}")
    sys.exit(1)

# ============================================================================
# STEP 2: Create Initial State
# ============================================================================
print("\n[STEP 2] Creating initial state...")
PROSPECT_NAME = "TestBank"

try:
    initial_state = create_initial_state(
        prospect_name=PROSPECT_NAME,
        user_preferences={}
    )
    thread_id = initial_state["execution_id"]
    print(f"✅ State created")
    print(f"   Prospect: {PROSPECT_NAME}")
    print(f"   Thread ID: {thread_id[:8]}...")
except Exception as e:
    print(f"❌ State creation failed: {e}")
    sys.exit(1)

# ============================================================================
# STEP 3: Run to Checkpoint 1
# ============================================================================
print("\n[STEP 3] Running workflow to Checkpoint 1...")
print("   This will execute Agents 1-5:")
print("   - Agent 1: Scraper (may use cache)")
print("   - Agent 2: Cleaner")
print("   - Agent 3: Query Generator (LLM calls)")
print("   - Agent 4: Research (Tavily calls)")
print("   - Agent 5: Analysis (LLM calls)")
print("\n⚠️  This takes 5-10 minutes and costs ~$0.30")

try:
    state = orchestrator.run(initial_state, thread_id)
    
    # Verify paused at checkpoint 1
    checkpoint = orchestrator.compiled_graph.get_state({"configurable": {"thread_id": thread_id}})
    next_node = checkpoint.next[0] if checkpoint.next else "END"
    
    if next_node == "checkpoint_1":
        print(f"\n✅ Paused before checkpoint_1")
        
        # Validate we have analysis
        analysis_json = state.get("analysis_json")
        if not analysis_json:
            print("❌ No analysis data!")
            sys.exit(1)
        
        print(f"\n📊 Analysis Results:")
        print(f"   Use cases scored: {len(analysis_json.items)}")
        print(f"\n   Top 3 Recommendations:")
        for i, item in enumerate(analysis_json.items[:3], 1):
            print(f"   {i}. {item.usecase} (score: {item.score:.2f})")
        
    else:
        print(f"❌ Workflow paused at wrong node: {next_node}")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Workflow failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# CHECKPOINT 1: Simulate User Input
# ============================================================================
print("\n" + "="*80)
print("CHECKPOINT 1: Use Case Selection")
print("="*80)

# Auto-select AI's top 3
analysis_json = state["analysis_json"]
top_3_ai = [item.usecase for item in analysis_json.items[:3]]

print("\n[USER ACTION] Accepting AI recommendations:")
for i, uc in enumerate(top_3_ai, 1):
    print(f"  {i}. {uc}")

user_input_cp1 = {
    "top_3_usecases": top_3_ai,
    "approved": True
}

# ============================================================================
# STEP 4: Resume to Checkpoint 2
# ============================================================================
print("\n[STEP 4] Resuming workflow to Checkpoint 2...")
print("   This will execute Agents 6-8:")
print("   - Agent 6: Product Mapper (LLM calls)")
print("   - Agent 7: Content Creator (3 LLM calls)")
print("   - Agent 8: Slide Maker (PPTX generation)")
print("\n⚠️  This takes 2-3 minutes and costs ~$0.20")

try:
    state = orchestrator.resume(user_input_cp1, thread_id)
    
    # Check if paused at checkpoint 2
    checkpoint = orchestrator.compiled_graph.get_state({"configurable": {"thread_id": thread_id}})
    next_node = checkpoint.next[0] if checkpoint.next else "END"
    
    if next_node == "checkpoint_2":
        print(f"\n✅ Paused before checkpoint_2")
        
        # Validate we have PPTX
        pptx_path = state.get("pptx_path")
        if not pptx_path:
            print("❌ No PPTX generated!")
            sys.exit(1)
        
        print(f"\n📄 PPTX Ready:")
        print(f"   Path: {pptx_path}")
        print(f"   Slides: {len(state['content_json'].slides)}")
        
    else:
        print(f"❌ Workflow paused at wrong node: {next_node}")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Resume failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# CHECKPOINT 2: Simulate User Input
# ============================================================================
print("\n" + "="*80)
print("CHECKPOINT 2: Final Review")
print("="*80)

print("\n[USER ACTION] Approving presentation")

user_input_cp2 = {
    "action": CheckpointAction.APPROVE
}

# ============================================================================
# STEP 5: Final Resume (Complete Workflow)
# ============================================================================
print("\n[STEP 5] Final resume (completing workflow)...")

try:
    final_state = orchestrator.resume(user_input_cp2, thread_id)
    
    # Check if completed
    if not final_state.get("needs_human_review"):
        print("\n✅ Workflow complete!")
        
        # Display final summary
        print("\n" + "="*80)
        print("WORKFLOW SUMMARY")
        print("="*80)
        
        print(f"\n📊 Statistics:")
        print(f"   Prospect: {final_state['prospect_name']}")
        print(f"   Execution ID: {final_state['execution_id'][:8]}...")
        print(f"   Total tokens: {final_state.get('total_tokens_used', 0)}")
        
        print(f"\n✅ Outputs:")
        print(f"   IntentHQ cached: {final_state.get('intenthq_cache_hit', False)}")
        print(f"   Prospect cached: {final_state.get('prospect_cache_hit', False)}")
        print(f"   Use cases analyzed: {len(final_state['analysis_json'].items)}")
        print(f"   Selected use cases: {len(final_state['top_3_usecases'])}")
        print(f"   Products mapped: {len(final_state['product_mapping_json'].solutions)}")
        print(f"   Slides generated: {len(final_state['content_json'].slides)}")
        print(f"   PPTX: {final_state['pptx_path']}")
        
        print("\n" + "="*80)
        print("🎉 ALL TESTS PASSED!")
        print("="*80)
        
    else:
        print("❌ Workflow still waiting for input!")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Final resume failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ Full workflow test complete!")