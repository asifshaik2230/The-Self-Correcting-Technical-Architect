"""
Coder Node: Generates implementation code based on the research plan.
"""

import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from src.state import AgentState
from src.config import settings

logger = logging.getLogger(__name__)


def coder_node(state: AgentState) -> AgentState:
    """
    Coder node: Generates implementation code and comprehensive tests.
    
    This node:
    1. Reviews the research and plan from previous node
    2. Generates production-ready core function code
    3. Generates a separate comprehensive test suite
    4. Stores both code and tests in state for execution
    
    Args:
        state: Current agent state with research findings
        
    Returns:
        AgentState: Updated state with generated code and tests
    """
    logger.info("Coder node: Generating implementation code and tests...")
    
    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.3  # Lower temperature for code generation
    )
    
    # Build context from previous analysis
    previous_analysis = state["messages"][-1]["content"] if state["messages"] else ""
    
    # Step 1: Generate the core implementation code
    code_prompt = f"""You are an expert Python developer. Based on the analysis, generate production-ready core function code.

Task: {state['task_description']}

Technical Specification:
{state['technical_spec']}

Previous Analysis:
{previous_analysis}

Generate complete, runnable Python code that:
1. Follows PEP 8 style guidelines
2. Includes comprehensive error handling
3. Has detailed docstrings
4. Includes type hints
5. Is well-commented
6. Handles all edge cases mentioned in the spec

IMPORTANT: Return ONLY the Python code itself, with NO markdown formatting, NO code blocks (```), NO explanations, and NO additional text. The code should be directly executable."""

    # Get core code from LLM
    code_response = llm.invoke([HumanMessage(content=code_prompt)])
    generated_code = code_response.content
    
    # Step 2: Generate comprehensive test suite
    test_prompt = f"""You are an expert QA engineer. Generate a comprehensive test suite for the following code.

Task: {state['task_description']}

Technical Specification:
{state['technical_spec']}

Core Implementation Code:
{generated_code}

Generate a complete test_suite.py file that:
1. Uses pytest framework
2. Tests all functionality including edge cases
3. Tests error conditions and input validation
4. Includes multiple test cases for each function
5. Has descriptive test names and assertions
6. Covers the technical specification requirements

IMPORTANT: Return ONLY the Python test code itself, with NO markdown formatting, NO code blocks (```), NO explanations, and NO additional text. The test code should be directly executable."""

    # Get test code from LLM
    test_response = llm.invoke([HumanMessage(content=test_prompt)])
    generated_test_code = test_response.content
    
    # Store in history and state
    state["code_history"].append(state["code"]) if state["code"] else None
    state["code"] = generated_code
    state["test_code"] = generated_test_code
    
    # Store explanation
    state["code_explanation"] = (
        f"Code and tests generated for: {state['task_description']}\n"
        f"Based on the research plan. Includes comprehensive test suite."
    )
    
    # Update state
    state["messages"].append({
        "role": "assistant",
        "content": f"Generated code:\n{generated_code}\n\nGenerated tests:\n{generated_test_code}",
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "metadata": {
            "node": "coder", 
            "code_length": len(generated_code),
            "test_length": len(generated_test_code)
        }
    })
    
    state["status"] = "executing"
    state["last_updated"] = __import__("datetime").datetime.now().isoformat()
    state["retry_count"] += 1
    
    logger.info(f"Coder node: Code ({len(generated_code)} chars) and tests ({len(generated_test_code)} chars) generated")
    
    return state
