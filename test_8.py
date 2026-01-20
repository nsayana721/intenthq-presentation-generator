"""
Agent 8 (Slide Maker) Test
Tests PPTX generation with mock content.
"""

import sys
sys.path.insert(0, '/home/claude/intenthq-presentation-generator')

from src.agents.slide_maker_agent import SlideMakerAgent
from src.state.schemas import create_initial_state, ContentCreatorOutput, SlideContent
from pathlib import Path

print("="*80)
print("AGENT 8 (SLIDE MAKER) TEST")
print("="*80)

# ============================================================================
# STEP 1: Check Template
# ============================================================================
print("\n[STEP 1] Checking template file...")
template_path = Path("intenthq-presentation-generator/data/templates/Final_Template_V2_0.pptx")

if template_path.exists():
    print(f"✅ Template found: {template_path}")
else:
    print(f"❌ Template NOT found: {template_path}")
    print("\n⚠️  Please copy Final_Template_V2_0.pptx to:")
    print(f"   {template_path.absolute()}")
    print("\nCommand:")
    print(f"   cp Final_Template_V2_0.pptx {template_path}")
    sys.exit(1)

# ============================================================================
# STEP 2: Create Mock Content
# ============================================================================
print("\n[STEP 2] Creating mock slide content...")

mock_content = ContentCreatorOutput(
    brand="TestBank",
    generated_at="2026-01-20T00:00:00",
    slides=[
        # Slide 1: Title
        SlideContent(
            slide=1,
            title="Intent HQ x TestBank",
            content=""
        ),
        
        # Slide 2: Agenda
        SlideContent(
            slide=2,
            title="Agenda",
            bullets=[
                "Macro industry context",
                "Top pain use cases",
                "Intent HQ platform",
                "Product solutions",
                "Next steps"
            ]
        ),
        
        # Slide 3: Industry Context
        SlideContent(
            slide=3,
            title="Industry & Prospect Context",
            content="Banking sector facing digital transformation challenges with rising customer acquisition costs.",
            bullets=[
                "Customer acquisition costs increased 35% year-over-year",
                "Cookie deprecation impacting targeting effectiveness",
                "Regulatory pressure on data privacy and compliance"
            ]
        ),
        
        # Slide 4-6: Pain Slides
        SlideContent(
            slide=4,
            title="Customer Acquisition Challenges",
            bullets=[
                "CAC has risen from £120 to £162 per customer in 12 months",
                "Traditional paid media channels showing diminishing returns",
                "Difficulty measuring true customer lifetime value across channels"
            ]
        ),
        
        SlideContent(
            slide=5,
            title="Data Monetization Gaps",
            bullets=[
                "First-party data underutilized for revenue generation",
                "Lack of clear data strategy limiting partnership opportunities",
                "Privacy concerns restricting data sharing initiatives"
            ]
        ),
        
        SlideContent(
            slide=6,
            title="Consumer Research Limitations",
            bullets=[
                "Small, biased panels providing incomplete customer insights",
                "Slow turnaround times for market research studies",
                "Limited ability to understand real-time consumer behavior"
            ]
        ),
        
        # Slide 7-9: STATIC (About, Platform, Why)
        SlideContent(
            slide=7,
            title="About Intent HQ",
            content="STATIC_TEMPLATE"
        ),
        
        SlideContent(
            slide=8,
            title="Platform Overview",
            content="STATIC_TEMPLATE"
        ),
        
        SlideContent(
            slide=9,
            title="Why Intent HQ",
            content="STATIC_TEMPLATE"
        ),
        
        # Slide 10: Primary Solution
        SlideContent(
            slide=10,
            title="Primary Product Solution",
            bullets=[
                "Intent Lift: Real-time behavioral intelligence to reduce CAC by 30-40%",
                "Proprietary audience segments with 95% accuracy across 80M+ consumers",
                "Privacy-first architecture ensuring full GDPR compliance"
            ]
        ),
        
        # Slide 11: Secondary Solutions
        SlideContent(
            slide=11,
            title="Complementary Product Solutions",
            bullets=[
                "Intent Edge: Advanced analytics for data monetization opportunities",
                "Intent Insights: Consumer research at scale with panel-free methodology",
                "Seamless integration with existing martech stack"
            ]
        ),
        
        # Slide 12: Thank You
        SlideContent(
            slide=12,
            title="Thank You",
            content="STATIC_TEMPLATE"
        )
    ]
)

print(f"✅ Created mock content with {len(mock_content.slides)} slides")

# ============================================================================
# STEP 3: Create State
# ============================================================================
print("\n[STEP 3] Creating workflow state...")

state = create_initial_state(
    prospect_name="TestBank",
    user_preferences={}
)

state["content_json"] = mock_content

print("✅ State created with content_json")

# ============================================================================
# STEP 4: Run Agent 8
# ============================================================================
print("\n[STEP 4] Running Agent 8...")
print("⚠️  This will create a PPTX file in data/outputs/")

try:
    agent8 = SlideMakerAgent()
    result_state = agent8.execute(state)
    
    pptx_path = result_state.get("pptx_path")
    
    if pptx_path and Path(pptx_path).exists():
        print(f"\n✅ SUCCESS!")
        print(f"   PPTX created: {pptx_path}")
        print(f"   File size: {Path(pptx_path).stat().st_size / 1024:.1f} KB")
    else:
        print(f"\n❌ FAILED: PPTX path not set or file doesn't exist")
        
except Exception as e:
    print(f"\n❌ Agent 8 execution failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# STEP 5: Validation
# ============================================================================
print("\n" + "="*80)
print("VALIDATION")
print("="*80)

if pptx_path:
    print("\n✅ Agent 8 Test PASSED!")
    print("\nNext steps:")
    print("1. Open the PPTX file and verify:")
    print("   - Slide 1: Title has 'TestBank'")
    print("   - Slides 2-6: Content updated")
    print("   - Slides 7-9: Static template content (unchanged)")
    print("   - Slides 10-11: Product solutions")
    print("   - Slide 12: Thank you (unchanged)")
    print("\n2. If all looks good, test full workflow (Agents 1-8)")
    print("   python test_agents_1_8.py")
else:
    print("\n❌ Agent 8 Test FAILED")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)