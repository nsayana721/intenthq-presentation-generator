"""
Agent 8: Slide Maker Agent
Assembles final PPTX from content using named shapes in template.
"""

from src.agents.base_agent import BaseAgent
from src.state.schemas import WorkflowState
from src.tools.pptx_handler import PPTXHandler
from config import settings
from datetime import datetime


class SlideMakerAgent(BaseAgent):
    """Creates final PPTX presentation."""
    
    def __init__(self):
        super().__init__(name="SlideMakerAgent")
        self.pptx_handler = PPTXHandler()
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Create final PPTX presentation.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with PPTX path
        """
        self.log_execution_start()
        
        content_json = state.get("content_json")
        if not content_json or not content_json.slides:
            self.add_error_to_state(state, "No slide content available")
            raise ValueError("Missing content_json in state")
        
        try:
            # Generate output filename
            prospect_name = state["prospect_name"].replace(" ", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{prospect_name}_IntentHQ_{timestamp}.pptx"
            
            output_path = settings.outputs_dir / filename
            
            # Create presentation
            pptx_path = self.pptx_handler.create_presentation(content_json, output_path)
            
            state["pptx_path"] = str(pptx_path)
            
            self.logger.info(f"Presentation created: {filename}")
            
            self.update_state_metadata(state)
            self.log_execution_end(success=True)
            
            return state
            
        except Exception as e:
            self.log_error(e)
            self.add_error_to_state(state, f"PPTX creation failed: {str(e)}")
            raise