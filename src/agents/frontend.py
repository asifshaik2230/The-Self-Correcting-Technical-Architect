"""
Frontend Engineer Node: Generates UI/UX code based on the research plan.
"""

import logging
import re
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from src.state import AgentState
from src.config import settings

logger = logging.getLogger(__name__)


def extract_code_block(text: str, block_type: str = "UI") -> str:
    """
    Extract code from markdown code block in LLM response.

    Looks for patterns like:
    ```python
    # UI
    code here
    ```
    or
    ```python
    # UI_TESTS
    code here
    ```

    Args:
        text: Raw text from LLM response
        block_type: "UI" or "UI_TESTS" to identify which block to extract

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


def frontend_node(state: AgentState) -> AgentState:
    """
    Frontend Engineer node: Generates UI/UX code and tests.

    This node is EXECUTION-FREE. It ONLY:
    1. Prompts the LLM to generate UI code and tests
    2. Parses the LLM's text response to extract code blocks
    3. Stores extracted strings in state

    The actual execution happens in the executor_node.

    Args:
        state: Current agent state with research findings

    Returns:
        AgentState: Updated state with generated UI code and tests (as strings only)
    """
    logger.info("Frontend Engineer node: Generating UI/UX code and tests...")

    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.2
    )

    previous_analysis = state["messages"][-1]["content"] if state["messages"] else ""

    ui_prompt = f"""You are a Senior Frontend Engineer specializing in UI/UX development. Based on the analysis, generate production-ready UI code.

Task: {state['task_description']}

Technical Specification:
{state['technical_spec']}

Previous Analysis:
{previous_analysis}

Generate complete, runnable Python UI code that:
1. Uses Streamlit for web interfaces (preferred for Python applications)
2. Includes modern UI/UX design principles
3. Has responsive layouts and good visual hierarchy
4. Includes proper error handling and user feedback
5. Has detailed docstrings and comments
6. Handles all user interaction edge cases mentioned in the spec
7. Uses appropriate Streamlit components (st.columns, st.tabs, etc.)
8. Includes input validation and user-friendly error messages

Return the UI code in a markdown code block with a # UI comment marker:

```python
# UI
<your UI code here>
```

IMPORTANT: Use the markdown format above. Do NOT include any additional text before or after the code block."""

    ui_response = llm.invoke([HumanMessage(content=ui_prompt)])
    llm_ui_response = ui_response.content
    generated_ui_code = extract_code_block(llm_ui_response, "UI")

    if not generated_ui_code:
        logger.error("Failed to extract UI code from LLM response")
        generated_ui_code = llm_ui_response

    ui_test_prompt = f"""You are a Senior QA Engineer specializing in UI testing. Generate a comprehensive test suite that validates the UI components.

Task: {state['task_description']}

Technical Specification:
{state['technical_spec']}

UI Implementation Code:
{generated_ui_code}

CRITICAL UI TEST GENERATION RULES:

1. **DO NOT import the UI functions** - They are already loaded in the global namespace
2. **Use only simple assert statements** - NOT unittest or pytest decorators
3. **Wrap all tests in try...except AssertionError blocks** - Catch and print exact failures
4. **Print results for stdout capture** - System needs to see pass/fail messages
5. **Test all UI edge cases** from the spec, including:
   - Input validation (empty inputs, invalid formats, boundary values)
   - UI state changes and interactions
   - Error handling and user feedback
   - Component rendering and layout

CRITICAL TESTING RULES:

**STREAMLIT MOCKING**: For Streamlit components, use appropriate mocking or simulate the expected behavior without actually running Streamlit.

**NO EXTERNAL TEST LIBRARIES**: Stick to standard `assert` statements wrapped in standard `try/except` blocks.

UI TEST CODE STRUCTURE - Generate tests following this pattern:

```python
# UI_TESTS
import math
from unittest.mock import patch, MagicMock

# Test 1: UI Input Validation
try:
    # Simulate user input validation logic
    result = validate_input_function("valid_input")
    assert result == True, f"Expected True for valid input, got {result}"
    print("✓ Test 1 passed: Valid input validation")
except AssertionError as e:
    print(f"✗ Test 1 FAILED: {e}")

# Test 2: UI Error Handling
try:
    result = validate_input_function("")
    assert result == False, f"Expected False for empty input, got {result}"
    print("✓ Test 2 passed: Empty input handling")
except AssertionError as e:
    print(f"✗ Test 2 FAILED: {e}")

# Test 3: UI Component Logic (mock Streamlit if needed)
try:
    with patch('streamlit.text_input', return_value='test_value') as mock_input:
        result = process_ui_input()
        assert result == 'processed_test_value', f"Expected processed_test_value, got {result}"
    print("✓ Test 3 passed: UI component logic")
except AssertionError as e:
    print(f"✗ Test 3 FAILED: {e}")

print("\\nAll UI tests completed.")
```

REQUIREMENTS:
- Assume all UI functions from the code above are available in global namespace
- Do NOT write import statements or function definitions in the test code
- Focus on testing the business logic and validation functions
- Mock Streamlit components when necessary
- Make assertions clear with descriptive failure messages
- Print one line per test result (✓ for pass, ✗ for fail)
- Include the assertion error message in the ✗ output
- Wrap entire test section in markdown code block with # UI_TESTS comment marker

RETURN FORMAT: Use the markdown format with # UI_TESTS marker shown above."""

    ui_test_response = llm.invoke([HumanMessage(content=ui_test_prompt)])
    llm_ui_test_response = ui_test_response.content
    generated_ui_test_code = extract_code_block(llm_ui_test_response, "UI_TESTS")

    if not generated_ui_test_code:
        logger.error("Failed to extract UI test code from LLM response")
        generated_ui_test_code = llm_ui_test_response

    if state["code"]:
        state["code_history"].append(state["code"])

    state["code"] = generated_ui_code
    state["test_code"] = generated_ui_test_code
    state["code_explanation"] = (
        f"Frontend UI code and tests generated for: {state['task_description']}\n"
        f"Based on the research plan. Includes comprehensive UI test suite.\n"
        f"Code extracted from LLM output via markdown code block parsing."
    )

    state["messages"].append({
        "role": "assistant",
        "content": "Generated frontend UI code and tests",
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "node": "frontend",
            "code_length": len(generated_ui_code),
            "test_length": len(generated_ui_test_code),
            "extraction_method": "markdown_code_block_parsing"
        }
    })

    state["status"] = "executing"
    state["last_updated"] = datetime.now().isoformat()
    state["retry_count"] += 1

    logger.info(
        f"Frontend Engineer node: UI code ({len(generated_ui_code)} chars) and tests ({len(generated_ui_test_code)} chars) "
        f"generated and parsed (NO EXECUTION - text-only storage)"
    )

    return state