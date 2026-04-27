"""
State management for the Self-Correcting Technical Architect agent system.

Defines the TypedDict for the agent's shared state across the LangGraph workflow.
"""

from typing import TypedDict, Optional, Any
from datetime import datetime


class AgentMessage(TypedDict):
    """Represents a message in the agent workflow."""
    
    role: str  # "user", "assistant", "system", "reviewer"
    content: str
    timestamp: str
    metadata: Optional[dict[str, Any]]


class ExecutionResult(TypedDict):
    """Represents the result of code execution."""
    
    success: bool
    stdout: str
    stderr: str
    execution_time: float
    artifacts: Optional[dict[str, Any]]


class AgentState(TypedDict):
    """
    Central state dictionary for the Self-Correcting Technical Architect.
    
    This state is passed between nodes in the LangGraph workflow and maintains
    all relevant information about the current task execution.
    """
    
    # Core workflow identifiers
    task_id: str
    task_description: str
    technical_spec: str
    
    # Message history for context
    messages: list[AgentMessage]
    
    # Research state
    research_notes: Optional[str]  # Web search results and findings
    memory_hits: Optional[list[dict[str, Any]]]  # Retrieved memory entries
    routing_decision: str  # "frontend", "backend", or "fullstack"
    
    # Code-related state
    code: str  # Current implementation
    test_code: str  # Generated test suite
    code_history: list[str]  # Previous versions for rollback
    code_explanation: str  # Agent's explanation of the code
    
    # Execution tracking
    execution_logs: list[ExecutionResult]
    last_execution: Optional[ExecutionResult]
    
    # Validation & review state
    validation_errors: list[str]
    review_feedback: str
    spec_compliance_score: float  # 0.0 to 1.0
    
    # Retry and decision logic
    retry_count: int
    max_retries: int
    
    # Metadata
    start_time: str
    last_updated: str
    status: str  # "planning", "coding", "executing", "reviewing", "completed", "failed"
    
    # Final outputs
    final_code: Optional[str]
    final_report: Optional[str]
    success: bool


class ReviewCriteria(TypedDict):
    """Criteria for the reviewer node to validate code."""
    
    correctness: bool
    spec_compliance: bool
    performance: bool
    readability: bool
    error_handling: bool
    issues: list[str]
    score: float
