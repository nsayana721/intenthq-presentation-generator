"""
Base agent class with common functionality.
All 8 agents inherit from this.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from langchain_openai import ChatOpenAI
from src.state.schemas import WorkflowState
from config import settings
import logging
import time


class BaseAgent(ABC):
    """
    Base class for all autonomous agents.
    
    Each agent must implement:
    - execute(): Main logic
    - (optionally) validate_output(): Check quality
    """
    
    def __init__(self, name: str, model: Optional[str] = None, temperature: Optional[float] = None):
        """
        Initialize base agent.
        
        Args:
            name: Agent name (for logging)
            model: LLM model to use (defaults to settings)
            temperature: LLM temperature (defaults to settings)
        """
        self.name = name
        self.model = model or settings.llm_model
        self.temperature = temperature or settings.llm_temperature
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            api_key=settings.openai_api_key
        )
        
        # Setup logging
        self.logger = logging.getLogger(f"agent.{name}")
        self.logger.setLevel(logging.INFO)
        
        # Metrics
        self.execution_count = 0
        self.total_tokens = 0
        self.total_time = 0.0
    
    @abstractmethod
    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Main execution logic for the agent.
        Must be implemented by each agent.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        pass
    
    def validate_output(self, output: Any) -> bool:
        """
        Validate agent output.
        Can be overridden by specific agents.
        
        Args:
            output: Agent's output to validate
            
        Returns:
            True if valid, False otherwise
        """
        return output is not None
    
    def log_execution_start(self, context: Dict[str, Any] = None):
        """Log execution start."""
        self.logger.info(
            f"[{self.name}] Starting execution",
            extra=context or {}
        )
    
    def log_execution_end(self, success: bool, context: Dict[str, Any] = None):
        """Log execution end."""
        level = logging.INFO if success else logging.ERROR
        self.logger.log(
            level,
            f"[{self.name}] Execution {'completed' if success else 'failed'}",
            extra=context or {}
        )
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log error with context."""
        self.logger.error(
            f"[{self.name}] Error: {str(error)}",
            exc_info=True,
            extra=context or {}
        )
    
    def track_metrics(self, tokens: int, execution_time: float):
        """Track execution metrics."""
        self.execution_count += 1
        self.total_tokens += tokens
        self.total_time += execution_time
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics."""
        return {
            "name": self.name,
            "execution_count": self.execution_count,
            "total_tokens": self.total_tokens,
            "total_time": self.total_time,
            "avg_time": self.total_time / max(self.execution_count, 1)
        }
    
    def update_state_metadata(self, state: WorkflowState, tokens: int = 0):
        """Update state metadata after execution."""
        from datetime import datetime
        
        state["updated_at"] = datetime.now()
        state["total_tokens_used"] += tokens
        state["current_step"] = self.name.lower().replace(" ", "_")
    
    def add_error_to_state(self, state: WorkflowState, error: str, details: str = ""):
        """Add error to state error log."""
        from datetime import datetime
        
        state["error_log"].append({
            "agent": self.name,
            "error": error,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def __call__(self, state: WorkflowState) -> WorkflowState:
        """
        Make agent callable (for LangGraph compatibility).
        Wraps execute() with timing and error handling.
        """
        start_time = time.time()
        
        try:
            self.log_execution_start({"execution_id": state["execution_id"]})
            
            # Execute agent logic
            updated_state = self.execute(state)
            
            # Track metrics
            execution_time = time.time() - start_time
            self.track_metrics(tokens=0, execution_time=execution_time)  # Tokens tracked individually
            
            self.log_execution_end(success=True)
            return updated_state
            
        except Exception as e:
            self.log_error(e, {"execution_id": state["execution_id"]})
            self.add_error_to_state(state, str(e))
            
            # Re-raise for LangGraph to handle
            raise


class AgentError(Exception):
    """Custom exception for agent errors."""
    pass