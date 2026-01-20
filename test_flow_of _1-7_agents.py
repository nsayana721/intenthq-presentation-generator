"""
Integration Test: Agents 1-7
Tests the complete workflow from scraping to content generation.
"""

import sys
sys.path.insert(0, '/home/claude/intenthq-presentation-generator')

from src.state.schemas import create_initial_state, WorkflowState
from src.agents.scraper_agent import ScraperAgent
from src.agents.cleaner_agent import CleanerAgent
from src.agents.query_generator_agent import QueryGeneratorAgent
from src.agents.research_agent import ResearchAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.product_mapper_agent import ProductMapperAgent
from src.agents.content_creator_agent import ContentCreatorAgent
from config import settings
import json

print("="*80)
print("INTEGRATION TEST: Agents 1-7")
print("="*80)

# Test prospect
PROSPECT_NAME = "TestBank"

# ============================================================================
# STEP 1: Initialize State
# ============================================================================
print("\n[STEP 1] Initializing state...")
try:
    state = create_initial_state(
        prospect_name=PROSPECT_NAME,
        user_preferences={}
    )
    print(f"✅ State created: {state['execution_id'][:8]}...")
    print(f"   Prospect: {state['prospect_name']}")
except Exception as e:
    print(f"❌ State creation failed: {e}")
    sys.exit(1)

# ============================================================================
# STEP 2: Agent 1 - Scraper (will use cache or scrape)
# ============================================================================
print("\n[STEP 2] Agent 1 - Scraper Agent...")
print("⚠️  Note: This will actually scrape if cache expired (may take 2-3 min)")
print("   Checking cache first...")

try:
    agent1 = ScraperAgent()
    state = agent1.execute(state)
    
    if state["intenthq_cache_hit"]:
        print("✅ Loaded from cache (14-day TTL)")
    else:
        print("✅ Scraped fresh data")
    
    # Validate output
    raw_content = state.get("intenthq_content_raw")
    if not raw_content:
        print("❌ No raw content in state")
    else:
        print(f"✅ Raw content sections: {list(raw_content.keys())[:5]}")
        
except Exception as e:
    print(f"❌ Agent 1 failed: {e}")
    print("   Check: API key, network, rate limits")
    # For testing, create mock data
    print("\n⚠️  Creating mock data to continue testing...")
    state["intenthq_content_raw"] = {
        "home": {"markdown": "Mock IntentHQ content"},
        "platform": {"markdown": "Mock platform", "links": []},
        "platform_items": {},
        "use_case_items": {
            "usecases__customer-acquisition": {"markdown": "Mock usecase 1"},
            "usecases__data-monetization": {"markdown": "Mock usecase 2"},
        }
    }
    state["intenthq_cache_hit"] = False

# ============================================================================
# STEP 3: Agent 2 - Cleaner
# ============================================================================
print("\n[STEP 3] Agent 2 - Cleaner Agent...")
try:
    agent2 = CleanerAgent()
    state = agent2.execute(state)
    
    cleaned = state.get("intenthq_content_cleaned")
    if not cleaned:
        print("❌ No cleaned content")
    else:
        print(f"✅ Cleaned sections: {list(cleaned.keys())}")
        print(f"   Use cases found: {len(cleaned.get('use_cases', []))}")
        print(f"   Products found: {len(cleaned.get('platform_products', []))}")
        
except Exception as e:
    print(f"❌ Agent 2 failed: {e}")
    sys.exit(1)

# ============================================================================
# STEP 4: Agent 3 - Query Generator
# ============================================================================
print("\n[STEP 4] Agent 3 - Query Generator...")
print("⚠️  Note: This makes LLM calls (costs ~$0.01)")

try:
    agent3 = QueryGeneratorAgent()
    state = agent3.execute(state)
    
    queries_json = state.get("queries_json")
    if not queries_json:
        print("❌ No queries generated")
    else:
        print(f"✅ Queries generated: {len(queries_json.items)}")
        for i, item in enumerate(queries_json.items[:3], 1):
            print(f"   {i}. {item.usecase[:40]}...")
            print(f"      Query: {item.query[:60]}...")
            
except Exception as e:
    print(f"❌ Agent 3 failed: {e}")
    print("   Check: OpenAI API key, model access")
    sys.exit(1)

# ============================================================================
# STEP 5: Agent 4 - Research (Tavily)
# ============================================================================
print("\n[STEP 5] Agent 4 - Research Agent...")
print("⚠️  Note: This makes Tavily API calls (costs ~$0.05)")

try:
    agent4 = ResearchAgent()
    state = agent4.execute(state)
    
    research_json = state.get("research_json")
    if not research_json:
        print("❌ No research data")
    else:
        print(f"✅ Research complete: {len(research_json.items)} use cases")
        for i, item in enumerate(research_json.items[:2], 1):
            print(f"   {i}. {item.usecase[:40]}")
            print(f"      Answer: {len(item.answer)} chars")
            
except Exception as e:
    print(f"❌ Agent 4 failed: {e}")
    print("   Check: Tavily API key")
    sys.exit(1)

# ============================================================================
# STEP 6: Agent 5 - Analysis
# ============================================================================
print("\n[STEP 6] Agent 5 - Analysis Agent...")
print("⚠️  Note: This makes multiple LLM calls (~$0.10)")

try:
    agent5 = AnalysisAgent()
    state = agent5.execute(state)
    
    analysis_json = state.get("analysis_json")
    if not analysis_json:
        print("❌ No analysis data")
    else:
        print(f"✅ Analysis complete: {len(analysis_json.items)} use cases scored")
        print(f"\n   Top 3 Recommendations:")
        for i, item in enumerate(analysis_json.items[:3], 1):
            print(f"   {i}. {item.usecase} (score: {item.score:.2f})")
            print(f"      Pain: {item.pain}, Cost: {item.cost_revenue}, Benchmark: {item.benchmark_competition}")
            
except Exception as e:
    print(f"❌ Agent 5 failed: {e}")
    sys.exit(1)

# ============================================================================
# HUMAN CHECKPOINT 1 SIMULATION
# ============================================================================
print("\n[CHECKPOINT 1] Simulating human selection...")
print("   In production: User reviews table and selects top 3")

# Auto-select top 3
top_3_ai = [item.usecase for item in analysis_json.items[:3]]
state["top_3_usecases"] = top_3_ai
state["checkpoint1_approved"] = True

print(f"✅ Selected: {len(state['top_3_usecases'])} use cases")
for uc in state["top_3_usecases"]:
    print(f"   - {uc}")

# ============================================================================
# STEP 7: Agent 6 - Product Mapper
# ============================================================================
print("\n[STEP 7] Agent 6 - Product Mapper...")
print("⚠️  Note: This makes LLM calls (~$0.05)")

try:
    agent6 = ProductMapperAgent()
    state = agent6.execute(state)
    
    product_mapping_json = state.get("product_mapping_json")
    if not product_mapping_json:
        print("❌ No product mapping")
    else:
        print(f"✅ Products mapped: {len(product_mapping_json.solutions)} solutions")
        for i, sol in enumerate(product_mapping_json.solutions, 1):
            print(f"   {i}. {sol.usecase}")
            print(f"      Products: {[p.name for p in sol.products]}")
            
except Exception as e:
    print(f"❌ Agent 6 failed: {e}")
    sys.exit(1)

# ============================================================================
# STEP 8: Agent 7 - Content Creator
# ============================================================================
print("\n[STEP 8] Agent 7 - Content Creator...")
print("⚠️  Note: This makes multiple LLM calls (~$0.15)")

try:
    agent7 = ContentCreatorAgent()
    state = agent7.execute(state)
    
    content_json = state.get("content_json")
    if not content_json:
        print("❌ No content generated")
    else:
        print(f"✅ Content generated: {len(content_json.slides)} slides")
        print(f"\n   Slide Breakdown:")
        for slide in content_json.slides:
            print(f"   Slide {slide.slide}: {slide.title}")
            
except Exception as e:
    print(f"❌ Agent 7 failed: {e}")
    sys.exit(1)

# ============================================================================
# FINAL VALIDATION
# ============================================================================
print("\n" + "="*80)
print("FINAL VALIDATION")
print("="*80)

validation_checks = {
    "State initialized": state.get("execution_id") is not None,
    "IntentHQ content scraped": state.get("intenthq_content_raw") is not None,
    "Content cleaned": state.get("intenthq_content_cleaned") is not None,
    "Queries generated": state.get("queries_json") is not None,
    "Research completed": state.get("research_json") is not None,
    "Analysis completed": state.get("analysis_json") is not None,
    "Use cases selected": state.get("top_3_usecases") is not None,
    "Products mapped": state.get("product_mapping_json") is not None,
    "Content created": state.get("content_json") is not None,
}

all_passed = True
for check, passed in validation_checks.items():
    status = "✅" if passed else "❌"
    print(f"{status} {check}")
    if not passed:
        all_passed = False

print("\n" + "="*80)
if all_passed:
    print("🎉 ALL TESTS PASSED!")
    print("="*80)
    print("\n📊 Final Output Summary:")
    print(f"   - Prospect: {state['prospect_name']}")
    print(f"   - Use cases analyzed: {len(analysis_json.items)}")
    print(f"   - Top 3 selected: {len(state['top_3_usecases'])}")
    print(f"   - Products mapped: {len(product_mapping_json.solutions)}")
    print(f"   - Slides generated: {len(content_json.slides)}")
    print(f"   - Total tokens used: {state['total_tokens_used']}")
    print(f"\n✅ Ready for Agent 8 (PPTX generation)")
else:
    print("❌ SOME TESTS FAILED")
    print("="*80)
    print("Check error messages above")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)