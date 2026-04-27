"""
Backend Engineer Node: Generates backend code based on the research plan.
"""

import logging
import re
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from src.state import AgentState
from src.config import settings

logger = logging.getLogger(__name__)


def extract_code_block(text: str, block_type: str = "BACKEND") -> str:
    """
    Extract code from markdown code block in LLM response.

    Looks for patterns like:
    ```python
    # BACKEND
    code here
    ```
    or
    ```python
    # BACKEND_TESTS
    code here
    ```

    Args:
        text: Raw text from LLM response
        block_type: "BACKEND" or "BACKEND_TESTS" to identify which block to extract

    Returns:
        str: Extracted Python code, or empty string if not found
    """
    pattern = rf"```python\s*(?:#\s*{block_type})?\s*(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)

    if matches:
        code = matches[0].strip()
        return code

    logger.warning(f"Could not extract {block_type} code block from LLM response")
    return ""


def backend_node(state: AgentState) -> AgentState:
    """
    Backend Engineer node: Generates backend code and tests.

    This node is EXECUTION-FREE. It ONLY:
    1. Prompts the LLM to generate backend code and tests
    2. Parses the LLM's text response to extract code blocks
    3. Stores extracted strings in state

    The actual execution happens in the executor_node.

    Args:
        state: Current agent state with research findings

    Returns:
        AgentState: Updated state with generated backend code and tests (as strings only)
    """
    logger.info("Backend Engineer node: Generating backend code and tests...")

    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.2
    )

    previous_analysis = state["messages"][-1]["content"] if state["messages"] else ""

    backend_prompt = f"""You are a Senior Backend Engineer specializing in algorithms, data structures, and server-side logic. Based on the analysis, generate production-ready backend code.

Task: {state['task_description']}

Technical Specification:
{state['technical_spec']}

Previous Analysis:
{previous_analysis}

Generate complete, runnable Python backend code that:
1. Implements efficient algorithms and data structures
2. Includes comprehensive error handling and input validation
3. Has detailed docstrings with type hints
4. Is well-commented and follows PEP 8
5. Handles all edge cases mentioned in the spec
6. Includes database operations if required (PostgreSQL preferred)
7. Implements APIs or data processing logic as needed
8. Is optimized for performance and scalability

Return the backend code in a markdown code block with a # BACKEND comment marker:

```python
# BACKEND
<your backend code here>
```

IMPORTANT: Use the markdown format above. Do NOT include any additional text before or after the code block."""

    backend_response = llm.invoke([HumanMessage(content=backend_prompt)])
    llm_backend_response = backend_response.content
    generated_backend_code = extract_code_block(llm_backend_response, "BACKEND")

    if not generated_backend_code:
        logger.error("Failed to extract backend code from LLM response")
        generated_backend_code = llm_backend_response

    backend_test_prompt = f"""You are a Senior QA Engineer specializing in backend testing. Generate a comprehensive test suite that validates the backend algorithms and logic.

Task: {state['task_description']}

Technical Specification:
{state['technical_spec']}

Backend Implementation Code:
{generated_backend_code}

CRITICAL TEST GENERATION RULES:

1. **DO NOT import the backend functions** - They are already loaded in the global namespace
2. **Use only simple assert statements** - NOT unittest or pytest decorators
3. **Wrap all tests in try...except AssertionError blocks** - Catch and print exact failures
4. **Print results for stdout capture** - System needs to see pass/fail messages
5. **Test all backend edge cases** from the spec, including:
   - Algorithm correctness (boundary conditions, edge cases)
   - Data structure operations (empty, single element, large datasets)
   - Error handling (invalid inputs, exceptions)
   - Performance characteristics where applicable

CRITICAL TESTING RULES:

**TIME MOCKING**: For any time-dependent logic, NEVER use `time.sleep()`. You MUST use `unittest.mock.patch` to mock `time.time` or `datetime` to simulate the passage of time instantly.

**FLOATING POINT ASSERTIONS**: NEVER use strict equality (`==`) for floats. You MUST use `math.isclose(actual, expected, rel_tol=1e-5, abs_tol=1e-5)` to account for precision issues.

**NO EXTERNAL TEST LIBRARIES**: Stick to standard `assert` statements wrapped in standard `try/except` blocks.

TEST CODE STRUCTURE - Generate tests following this pattern:

```python
# BACKEND_TESTS
import math
from unittest.mock import patch

# Test 1: Algorithm correctness - normal case
try:
    result = algorithm_function(test_input)
    assert result == expected_value, f"Expected {expected_value}, got {result}"
    print("✓ Test 1 passed: Normal case")
except AssertionError as e:
    print(f"✗ Test 1 FAILED: {e}")

# Test 2: Edge case handling
try:
    result = algorithm_function(edge_case_input)
    assert result == expected_edge_result, f"Expected {expected_edge_result}, got {result}"
    print("✓ Test 2 passed: Edge case")
except AssertionError as e:
    print(f"✗ Test 2 FAILED: {e}")

# Test 3: Float comparison test (if applicable)
try:
    result = function_returning_float(float_input)
    assert math.isclose(result, expected_float, rel_tol=1e-5, abs_tol=1e-5), f"Expected {expected_float}, got {result}"
    print("✓ Test 3 passed: Float comparison")
except AssertionError as e:
    print(f"✗ Test 3 FAILED: {e}")

# Test 4: Time-dependent logic test (if applicable)
try:
    with patch('time.time') as mock_time:
        mock_time.return_value = 100.0
        result = time_dependent_function()
        assert result == expected_for_time_100, f"Expected {expected_for_time_100}, got {result}"
    print("✓ Test 4 passed: Time mocking")
except AssertionError as e:
    print(f"✗ Test 4 FAILED: {e}")

print("\\nAll backend tests completed.")
```

REQUIREMENTS:
- Assume all backend functions from the code above are available in global namespace
- Do NOT write import statements or function definitions in the test code
- Use simple variables and direct function calls
- Make assertions clear with descriptive failure messages
- Print one line per test result (✓ for pass, ✗ for fail)
- Include the assertion error message in the ✗ output
- Wrap entire test section in markdown code block with # BACKEND_TESTS comment marker
- ALWAYS use math.isclose() for floating-point comparisons
- ALWAYS use unittest.mock.patch for time-dependent logic

RETURN FORMAT: Use the markdown format with # BACKEND_TESTS marker shown above."""

    backend_test_response = llm.invoke([HumanMessage(content=backend_test_prompt)])
    llm_backend_test_response = backend_test_response.content
    generated_backend_test_code = extract_code_block(llm_backend_test_response, "BACKEND_TESTS")

    if not generated_backend_test_code:
        logger.error("Failed to extract backend test code from LLM response")
        generated_backend_test_code = llm_backend_test_response

    if state["code"]:
        state["code_history"].append(state["code"])

    state["code"] = generated_backend_code
    state["test_code"] = generated_backend_test_code
    state["code_explanation"] = (
        f"Backend code and tests generated for: {state['task_description']}\n"
        f"Based on the research plan. Includes comprehensive backend test suite.\n"
        f"Code extracted from LLM output via markdown code block parsing."
    )

    state["messages"].append({
        "role": "assistant",
        "content": "Generated backend code and tests",
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "node": "backend",
            "code_length": len(generated_backend_code),
            "test_length": len(generated_backend_test_code),
            "extraction_method": "markdown_code_block_parsing"
        }
    })

    state["status"] = "executing"
    state["last_updated"] = datetime.now().isoformat()
    state["retry_count"] += 1

    logger.info(
        f"Backend Engineer node: Code ({len(generated_backend_code)} chars) and tests ({len(generated_backend_test_code)} chars) "
        f"generated and parsed (NO EXECUTION - text-only storage)"
    )

    return state