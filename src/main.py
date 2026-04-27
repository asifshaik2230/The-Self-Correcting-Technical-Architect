"""
Main entry point for the Self-Correcting Technical Architect.

Initializes and runs the LangGraph state machine with nodes for:
- Researcher (analyze requirements)
- Coder (generate code)
- Executor (run code in sandbox)
- Reviewer (validate against spec)
"""

# Suppress Pydantic V1 compatibility warnings BEFORE any imports
import os
os.environ["PYDANTIC_DISABLE_V1_WARNINGS"] = "1"

import logging
from datetime import datetime
from typing import Any

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from psycopg_pool import AsyncConnectionPool

from src.state import AgentState, AgentMessage, ExecutionResult
from src.config import settings
from src.agents.researcher import researcher_node
from src.agents.frontend import frontend_node
from src.agents.backend import backend_node
from src.agents.executor import executor_node
from src.agents.reviewer import reviewer_node

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_initial_state(
    task_description: str,
    technical_spec: str,
    task_id: str = "default_task"
) -> AgentState:
    """
    Create an initial agent state.
    
    Args:
        task_description: Description of the task to solve
        technical_spec: Technical specification for validation
        task_id: Unique identifier for the task
        
    Returns:
        AgentState: Initialized state dictionary
    """
    now = datetime.now().isoformat()
    
    return AgentState(
        task_id=task_id,
        task_description=task_description,
        technical_spec=technical_spec,
        messages=[
            AgentMessage(
                role="system",
                content=f"Task: {task_description}\n\nSpec: {technical_spec}",
                timestamp=now,
                metadata={"type": "initialization"}
            )
        ],
        research_notes=None,
        memory_hits=None,
        routing_decision="",
        code="",
        test_code="",
        code_history=[],
        code_explanation="",
        execution_logs=[],
        last_execution=None,
        validation_errors=[],
        review_feedback="",
        spec_compliance_score=0.0,
        retry_count=0,
        max_retries=settings.max_retries,
        start_time=now,
        last_updated=now,
        status="planning",
        final_code=None,
        final_report=None,
        success=False,
    )


def build_graph() -> StateGraph:
    """
    Build the LangGraph state machine with all nodes and edges.
    
    The workflow follows: Researcher → (conditional routing) → Frontend/Backend → Executor → Reviewer → (loop or end)
    
    Returns:
        StateGraph: Compiled graph ready for execution
    """
    graph = StateGraph(AgentState)
    
    # Add nodes to the graph
    graph.add_node("researcher", researcher_node)
    graph.add_node("frontend", frontend_node)
    graph.add_node("backend", backend_node)
    graph.add_node("executor", executor_node)
    graph.add_node("reviewer", reviewer_node)
    
    # Define edges (workflow transitions)
    # Conditional edge from researcher based on routing decision
    def route_to_coder(state: AgentState) -> str:
        """Route to appropriate engineer based on routing decision."""
        decision = state["routing_decision"]
        if decision == "frontend":
            return "frontend"
        elif decision == "backend":
            return "backend"
        else:  # "fullstack" or default
            return "backend"
    
    graph.add_conditional_edges("researcher", route_to_coder)
    
    # Both frontend and backend output to executor
    graph.add_edge("frontend", "executor")
    graph.add_edge("backend", "executor")
    graph.add_edge("executor", "reviewer")
    
    # Conditional edge from reviewer
    # If review passes and spec compliance > 0.8, finish
    # Otherwise, retry coding (max retries enforced) - route back to appropriate engineer
    def review_decision(state: AgentState) -> str:
        """Decide whether to retry or finish based on review feedback."""
        if state["success"]:
            return END
        elif state["retry_count"] >= state["max_retries"]:
            logger.warning(f"Max retries ({state['max_retries']}) reached. Ending workflow.")
            return END
        else:
            logger.info(f"Review failed. Retrying (attempt {state['retry_count'] + 1}/{state['max_retries']})")
            # Route back to the same engineer that was used
            decision = state["routing_decision"]
            if decision == "frontend":
                return "frontend"
            else:  # "backend" or "fullstack"
                return "backend"
    
    graph.add_conditional_edges("reviewer", review_decision)
    
    # Set entry point
    graph.set_entry_point("researcher")
    
    return graph.compile()


def initialize_llm() -> ChatGoogleGenerativeAI:
    """
    Initialize the Google Gemini language model.
    
    Returns:
        ChatGoogleGenerativeAI: Configured LLM instance
    """
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.7,
    )


async def run_agent(
    task_description: str,
    technical_spec: str,
    task_id: str = "default_task",
    thread_id: str = None
) -> dict[str, Any]:
    """
    Run the Self-Correcting Technical Architect agent.
    
    Args:
        task_description: Description of the task to solve
        technical_spec: Technical specification for validation
        task_id: Unique identifier for the task
        thread_id: Optional thread ID for persistent state (defaults to task_id)
        
    Returns:
        dict: Final state after agent execution
        
    Raises:
        ValueError: If required configuration is missing
    """
    if thread_id is None:
        thread_id = task_id
    
    try:
        logger.info(f"Initializing agent for task: {task_id}")
        logger.info(f"Task: {task_description}")
        
        # Create initial state
        initial_state = create_initial_state(task_description, technical_spec, task_id)
        
        # Run the graph with PostgreSQL persistence
        logger.info("Starting LangGraph execution with PostgreSQL checkpointer...")
        
        async with AsyncConnectionPool(settings.POSTGRES_URI, kwargs={"autocommit": True}) as pool:
            checkpointer = AsyncPostgresSaver(pool)
            await checkpointer.setup()
            
            # Build graph with checkpointer
            graph_instance = build_graph()
            compiled_graph = graph_instance.compile(checkpointer=checkpointer)
            
            config = {"configurable": {"thread_id": thread_id}}
            final_state = await compiled_graph.ainvoke(initial_state, config=config)
        
        logger.info(f"Agent execution completed. Status: {final_state['status']}")
        logger.info(f"Success: {final_state['success']}")
        
        # Export successful output
        if final_state["success"]:
            os.makedirs("output", exist_ok=True)
            output_file = f"output/{task_id}.py"
            with open(output_file, "w") as f:
                f.write(final_state["code"])
            
            final_report = (
                f"✅ AGENT COMPLETED SUCCESSFULLY\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Output File: {output_file}\n"
                f"Retry Count: {final_state['retry_count']}\n"
                f"Compliance Score: {final_state['spec_compliance_score']:.1%}\n"
            )
            final_state["final_report"] = final_report
            logger.info(final_report)
        else:
            final_report = (
                f"❌ AGENT FAILED TO COMPLETE\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Retry Count: {final_state['retry_count']}\n"
                f"Status: {final_state['status']}\n"
                f"Last Feedback: {final_state['review_feedback'][:200]}\n"
            )
            final_state["final_report"] = final_report
            logger.info(final_report)
        
        return final_state
        
    except Exception as e:
        logger.error(f"Error during agent execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Example usage (for testing)
    import asyncio
    
    EXAMPLE_TASK = "Write a Python function that calculates the Fibonacci sequence"
    EXAMPLE_SPEC = """
    Requirements:
    1. Function should accept n as parameter
    2. Should return list of first n Fibonacci numbers
    3. Should handle edge cases (n <= 0)
    4. Must include docstring
    5. Should be optimized for performance
    """
    
    result = asyncio.run(run_agent(EXAMPLE_TASK, EXAMPLE_SPEC, "fib_task_001"))
    print(f"\n=== Final Report ===\n{result.get('final_report', 'No report generated')}")
