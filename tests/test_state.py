"""Tests for state definitions."""

import pytest
from datetime import datetime
from src.state import AgentState, AgentMessage, ExecutionResult, ReviewCriteria


def test_agent_message_structure():
    """Test that AgentMessage can be created with required fields."""
    msg: AgentMessage = {
        "role": "assistant",
        "content": "Test message",
        "timestamp": datetime.now().isoformat(),
        "metadata": {"test": True}
    }
    
    assert msg["role"] == "assistant"
    assert msg["content"] == "Test message"
    assert msg["metadata"]["test"] is True


def test_execution_result_structure():
    """Test that ExecutionResult can be created with required fields."""
    result: ExecutionResult = {
        "success": True,
        "stdout": "Output",
        "stderr": "",
        "execution_time": 1.5,
        "artifacts": {"file": "data.txt"}
    }
    
    assert result["success"] is True
    assert result["execution_time"] == 1.5
    assert len(result["artifacts"]) == 1


def test_agent_state_initialization():
    """Test that AgentState can be properly initialized."""
    now = datetime.now().isoformat()
    
    state: AgentState = {
        "task_id": "test_001",
        "task_description": "Test task",
        "technical_spec": "Test specification",
        "messages": [],
        "code": "",
        "code_history": [],
        "code_explanation": "",
        "execution_logs": [],
        "last_execution": None,
        "validation_errors": [],
        "review_feedback": "",
        "spec_compliance_score": 0.0,
        "retry_count": 0,
        "max_retries": 3,
        "start_time": now,
        "last_updated": now,
        "status": "planning",
        "final_code": None,
        "final_report": None,
        "success": False,
    }
    
    assert state["task_id"] == "test_001"
    assert state["max_retries"] == 3
    assert state["status"] == "planning"


def test_review_criteria_structure():
    """Test that ReviewCriteria can be created properly."""
    criteria: ReviewCriteria = {
        "correctness": True,
        "spec_compliance": True,
        "performance": True,
        "readability": True,
        "error_handling": True,
        "issues": ["issue1", "issue2"],
        "score": 85.5
    }
    
    assert criteria["correctness"] is True
    assert criteria["score"] == 85.5
    assert len(criteria["issues"]) == 2
