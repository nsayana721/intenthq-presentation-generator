#!/usr/bin/env python3
"""Quick test for Agent 8 (Slide Maker)"""

import sys
sys.path.insert(0, '/home/claude/intenthq-presentation-generator')

from src.state.schemas import create_initial_state, ContentCreatorOutput, SlideContent
from src.agents.slide_maker_agent import SlideMakerAgent
from datetime import datetime

print("Testing Agent 8 (Slide Maker)...\n")

# Create mock content
content = ContentCreatorOutput(
    brand="TestBrand",
    generated_at=datetime.utcnow().isoformat(),
    slides=[
        SlideContent(slide=1, title="Intent HQ x TestBrand", content=""),
        SlideContent(slide=2, title="Agenda", bullets=["Item 1", "Item 2"]),
        SlideContent(slide=3, title="Industry Context", content="Test content", bullets=["Bullet 1", "Bullet 2", "Bullet 3"]),
        SlideContent(slide=4, title="Challenge 1", bullets=["Pain 1", "Pain 2", "Pain 3"]),
        SlideContent(slide=5, title="Challenge 2", bullets=["Pain 1", "Pain 2", "Pain 3"]),
        SlideContent(slide=6, title="Challenge 3", bullets=["Pain 1", "Pain 2", "Pain 3"]),
        SlideContent(slide=7, title="About", content="STATIC_TEMPLATE"),
        SlideContent(slide=8, title="Platform", content="STATIC_TEMPLATE"),
        SlideContent(slide=9, title="Why", content="STATIC_TEMPLATE"),
        SlideContent(slide=10, title="Intent Lift", bullets=["Solution 1", "Solution 2", "Solution 3"]),
        SlideContent(slide=11, title="Complementary", bullets=["Extra 1", "Extra 2", "Extra 3"]),
        SlideContent(slide=12, title="Thank You", content="STATIC_TEMPLATE"),
    ]
)

# Create state
state = create_initial_state("TestBrand", {})
state["content_json"] = content

# Run Agent 8
try:
    agent8 = SlideMakerAgent()
    state = agent8.execute(state)
    
    pptx_path = state.get("pptx_path")
    if pptx_path:
        print(f"✅ PPTX created: {pptx_path}")
    else:
        print("❌ No PPTX path in state")
        
except Exception as e:
    print(f"❌ Agent 8 failed: {e}")
    import traceback
    traceback.print_exc()