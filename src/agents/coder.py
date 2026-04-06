"""
Coder Node: Generates implementation code based on the research plan.
"""

import logging
import re
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from src.state import AgentState
from src.config import settings

logger = logging.getLogger(__name__)


def extract_code_block(text: str, block_type: str = "CORE") -> str:
    """
    Extract code from markdown code block in LLM response.
    
    Looks for patterns like:
    ```python
    # CORE
    code here
    ```
    or
    ```python
    # TESTS
    code here
    ```
    
    Args:
        text: Raw text from LLM response
        block_type: "CORE" or "TESTS" to identify which block to extract
        
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


def coder_node(state: AgentState) -> AgentState:
    """
    Coder node: Generates implementation code and comprehensive tests.
    
    This node is EXECUTION-FREE. It ONLY:
    1. Prompts the LLM to generate code and tests
    2. Parses the LLM's text response to extract code blocks
    3. Stores extracted strings in state
    
    The actual execution happens in the executor_node.
    
    Args:
        state: Current agent state with research findings
        
    Returns:
        AgentState: Updated state with generated code and tests (as strings only)
    """
    logger.info("Coder node: Generating implementation code and tests...")
    
    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.2
    )
    
    previous_analysis = state["messages"][-1]["content"] if state["messages"] else ""
    
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

Return the code in a markdown code block with a # CORE comment marker:

```python
# CORE
<your code here>
```

IMPORTANT: Use the markdown format above. Do NOT include any additional text before or after the code block."""

    code_response = llm.invoke([HumanMessage(content=code_prompt)])
    llm_code_response = code_response.content
    generated_code = extract_code_block(llm_code_response, "CORE")
    
    if not generated_code:
        logger.error("Failed to extract core code from LLM response")
        generated_code = llm_code_response

    test_prompt = f"""You are an expert QA engineer. Generate a comprehensive test suite that validates the core functions.

Task: {state['task_description']}

Technical Specification:
{state['technical_spec']}

Core Implementation Code:
{generated_code}

CRITICAL TEST GENERATION RULES:

1. **DO NOT import the core functions** - They are already loaded in the global namespace
2. **Use only simple assert statements** - NOT unittest or pytest decorators
3. **Wrap all tests in try...except AssertionError blocks** - Catch and print exact failures
4. **Print results for stdout capture** - System needs to see pass/fail messages
5. **Test all edge cases** from the spec, including:
   - Boundary conditions (n=0, n=1, empty inputs, etc.)
   - Invalid inputs (negative numbers, None, wrong types)
   - Normal cases and happy paths
   - Special requirements from specification

CRITICAL TESTING RULES:

**TIME MOCKING**: For any time-dependent logic, NEVER use `time.sleep()`. You MUST use `unittest.mock.patch` to mock `time.time` or `datetime` to simulate the passage of time instantly.

**FLOATING POINT ASSERTIONS**: NEVER use strict equality (`==`) for floats. You MUST use `math.isclose(actual, expected, rel_tol=1e-5, abs_tol=1e-5)` to account for precision issues.

**NO EXTERNAL TEST LIBRARIES**: Stick to standard `assert` statements wrapped in standard `try/except` blocks, do not invoke `unittest.main()`.

TEST CODE STRUCTURE - Generate tests following this pattern:

```python
# TESTS
import math
from unittest.mock import patch

# Test 1: Normal case
try:
    result = function_name(test_input)
    assert result == expected_value, f"Expected {{expected_value}}, got {{result}}"
    print("✓ Test 1 passed: Normal case")
except AssertionError as e:
    print(f"✗ Test 1 FAILED: {{e}}")

# Test 2: Float comparison test
try:
    result = function_name(float_input)
    assert math.isclose(result, expected_float, rel_tol=1e-5, abs_tol=1e-5), f"Expected {{expected_float}}, got {{result}}"
    print("✓ Test 2 passed: Float comparison")
except AssertionError as e:
    print(f"✗ Test 2 FAILED: {{e}}")

# Test 3: Time-dependent logic test (if applicable)
try:
    with patch('time.time') as mock_time:
        mock_time.return_value = 100.0
        result = function_that_uses_time()
        assert result == expected_for_time_100, f"Expected {{expected_for_time_100}}, got {{result}}"
    print("✓ Test 3 passed: Time mocking")
except AssertionError as e:
    print(f"✗ Test 3 FAILED: {{e}}")

print("\\nAll tests completed.")
```

REQUIREMENTS:
- Assume all core functions from the code above are available in global namespace
- Do NOT write import statements or function definitions in the test code
- Use simple variables and direct function calls
- Make assertions clear with descriptive failure messages
- Print one line per test result (✓ for pass, ✗ for fail)
- Include the assertion error message in the ✗ output
- Wrap entire test section in markdown code block with # TESTS comment marker
- ALWAYS use math.isclose() for floating-point comparisons
- ALWAYS use unittest.mock.patch for time-dependent logic

RETURN FORMAT: Use the markdown format with # TESTS marker shown above."""

    test_response = llm.invoke([HumanMessage(content=test_prompt)])
    llm_test_response = test_response.content
    generated_test_code = extract_code_block(llm_test_response, "TESTS")
    
    if not generated_test_code:
        logger.error("Failed to extract test code from LLM response")
        generated_test_code = llm_test_response

    if state["code"]:
        state["code_history"].append(state["code"])
    
    state["code"] = generated_code
    state["test_code"] = generated_test_code
    state["code_explanation"] = (
        f"Code and tests generated for: {state['task_description']}\n"
        f"Based on the research plan. Includes comprehensive test suite.\n"
        f"Code extracted from LLM output via markdown code block parsing."
    )
    
    state["messages"].append({
        "role": "assistant",
        "content": "Generated code and tests",
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "node": "coder",
            "code_length": len(generated_code),
            "test_length": len(generated_test_code),
            "extraction_method": "markdown_code_block_parsing"
        }
    })
    
    state["status"] = "executing"
    state["last_updated"] = datetime.now().isoformat()
    state["retry_count"] += 1
    
    logger.info(
        f"Coder node: Code ({len(generated_code)} chars) and tests ({len(generated_test_code)} chars) "
        f"generated and parsed (NO EXECUTION - text-only storage)"
    )
    
    return state
