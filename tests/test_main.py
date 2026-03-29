"""Tests for main module and graph structure."""

import pytest
from datetime import datetime
from src.state import AgentState
from src.main import create_initial_state, build_graph


def test_create_initial_state():
    """Test that initial state is properly created."""
    task_desc = "Test task description"
    spec = "Test specification"
    task_id = "test_001"
    
    state = create_initial_state(task_desc, spec, task_id)
    
    assert state["task_id"] == task_id
    assert state["task_description"] == task_desc
    assert state["technical_spec"] == spec
    assert state["status"] == "planning"
    assert state["success"] is False
    assert state["retry_count"] == 0
    assert len(state["messages"]) == 1  # System message
    

def test_initial_state_timestamp():
    """Test that timestamps are properly set."""
    state = create_initial_state("Task", "Spec")
    
    assert state["start_time"]
    assert state["last_updated"]
    # Verify ISO format
    datetime.fromisoformat(state["start_time"])
    datetime.fromisoformat(state["last_updated"])


def test_graph_building():
    """Test that the graph can be built without errors."""
    graph = build_graph()
    
    # Verify graph was created
    assert graph is not None
    # Graph should have compile method
    assert hasattr(graph, "ainvoke")


@pytest.mark.asyncio
async def test_graph_execution_structure():
    """Test the graph structure (not full execution)."""
    graph = build_graph()
    state = create_initial_state("Test task", "Test spec")
    
    # We don't actually invoke here to avoid API calls
    # Just verify the graph is properly configured
    assert graph is not None
