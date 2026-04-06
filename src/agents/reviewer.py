"""
Reviewer Node: Validates generated code against technical specifications.
"""

import logging
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from src.state import AgentState, ReviewCriteria
from src.config import settings
from src.tools.memory import save_to_memory

logger = logging.getLogger(__name__)


def reviewer_node(state: AgentState) -> AgentState:
    """
    Reviewer node: Validates code against technical specifications.
    
    This node:
    1. Reviews the generated code
    2. Checks spec compliance
    3. Identifies issues and improvements
    4. Provides feedback for potential retries
    5. Makes final go/no-go decision
    
    Args:
        state: Current agent state with execution results
        
    Returns:
        AgentState: Updated state with review feedback and success flag
    """
    logger.info("Reviewer node: Reviewing code against specification...")
    
    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.2
    )
    
    # Build review context
    execution_summary = ""
    test_results_available = False
    tests_passed = False
    
    if state.get("last_execution"):
        exec_result = state["last_execution"]
        execution_summary = f"""
        Execution Results:
        - Success: {exec_result['success']}
        - Stdout: {exec_result['stdout'][:500]}
        - Stderr: {exec_result['stderr'][:500] if exec_result['stderr'] else 'None'}
        - Time: {exec_result['execution_time']:.2f}s
        """
        
        # Check for test results in artifacts
        artifacts = exec_result.get('artifacts', {})
        if artifacts and 'test_execution' in artifacts:
            test_results_available = True
            test_exec = artifacts['test_execution']
            tests_passed = test_exec.get('success', False)
            execution_summary += f"""
        Test Results:
        - Tests Available: Yes
        - Tests Passed: {tests_passed}
        - Test Output: {test_exec.get('stdout', '')[:300]}
        - Test Errors: {test_exec.get('stderr', '')[:200] if test_exec.get('stderr') else 'None'}
        """
        else:
            execution_summary += "\n        Test Results: No automated tests executed"
    else:
        execution_summary = "\n        Execution Results: No execution results available"
    
    # TDD Priority: Check test results first
    if test_results_available:
        if tests_passed:
            # Tests passed - high confidence success, assign high score
            review_criteria = ReviewCriteria(
                correctness=True,
                spec_compliance=True,
                performance=True,
                readability=True,
                error_handling=True,
                issues=[],
                score=98.0  # Very high score for passing tests
            )
            review_content = "✅ CODE PASSED ALL TESTS - EXCELLENT\n\nTest-driven validation successful. All automated tests passed, confirming the implementation meets specifications and handles edge cases correctly. High confidence in code quality."
            is_successful = True
        else:
            # Tests failed - extract specific failure information
            test_exec_result = state["last_execution"]["artifacts"].get("test_execution", {})
            test_stdout = test_exec_result.get("stdout", "")
            test_stderr = test_exec_result.get("stderr", "")
            test_summary = test_exec_result.get("artifacts", {}).get("test_summary", {})
            
            # Check if core execution worked
            core_execution_success = False
            if state.get("last_execution") and state["last_execution"].get("artifacts"):
                core_exec = state["last_execution"]["artifacts"].get("core_execution")
                if core_exec and core_exec.get("success"):
                    core_execution_success = True
            
            if core_execution_success:
                # Core works but tests fail - extract specific assertion failures
                failure_messages = ""
                if "✗" in test_stdout:
                    # Extract test failure lines
                    lines = test_stdout.split("\n")
                    failure_lines = [line for line in lines if "✗" in line or "FAILED" in line]
                    failure_messages = "\n".join(failure_lines[:10])  # Top 10 failures
                
                if not failure_messages and test_stderr:
                    failure_messages = test_stderr
                
                review_criteria = ReviewCriteria(
                    correctness=True,  # Core logic works
                    spec_compliance=False,  # Doesn't pass tests yet
                    performance=True,
                    readability=True,
                    error_handling=False,  # Tests indicate issues
                    issues=["Test assertions failed - implementation doesn't match expected behavior"],
                    score=50.0  # Lower partial credit for test failures
                )
                
                review_content = f"""⚠️ TEST FAILURES - CORE WORKS, BUT TESTS FAIL

The core implementation executes successfully, but the test suite is failing. 

**Specific Failures Detected:**
{failure_messages if failure_messages else "See test output below for details."}

**Action Required:**
1. Review the test failure messages above
2. Verify the implementation matches the expected behavior
3. Check all edge cases from the specification are handled correctly
4. Ensure error handling works as specified

**Test Output:**
{test_stdout[-1000:] if test_stdout else "No output"}"""
                
                is_successful = False  # Allow retry
            else:
                # Both core and tests failed - critical issues
                review_criteria = ReviewCriteria(
                    correctness=False,
                    spec_compliance=False,
                    performance=False,
                    readability=False,
                    error_handling=False,
                    issues=["Core execution failed - implementation has critical issues"],
                    score=15.0
                )
                review_content = f"""❌ CRITICAL FAILURE - IMPLEMENTATION ERROR

Both the core code and tests failed to execute. The implementation has fundamental issues.

**Error Details:**
{test_stderr if test_stderr else "Check test output for error messages"}

**Action Required:**
- Review the syntax and logic of the implementation
- Ensure all required functions are defined
- Check for import or type errors"""
                
                is_successful = False
    else:
        # Fall back to subjective LLM review if no tests available
        # Create detailed review prompt
        prompt = f"""You are an expert code reviewer. Review the following code against the specification.

Technical Specification:
{state['technical_spec']}

Generated Code:
```python
{state['code']}
```

Execution Results:
{execution_summary}

Provide a structured review covering:
1. **Spec Compliance**: Does it meet all requirements? (yes/no)
2. **Correctness**: Is the logic correct? (yes/no)
3. **Error Handling**: Are edge cases handled? (yes/no)
4. **Performance**: Is it reasonably efficient? (yes/no)
5. **Code Quality**: Is it readable and well-documented? (yes/no)
6. **Overall Score**: 0-100
7. **Issues Found**: List any problems
8. **Feedback**: Specific suggestions for improvement

Format your response as a clear, structured review."""
        
        # Get review from LLM
        response = llm.invoke([HumanMessage(content=prompt)])
        review_content = response.content
        
        # Parse review (simplified - in production use structured output)
        review_criteria = ReviewCriteria(
            correctness="correct" in review_content.lower() or "yes" in review_content.lower(),
            spec_compliance="meets" in review_content.lower() or "complies" in review_content.lower(),
            performance="efficient" in review_content.lower(),
            readability="readable" in review_content.lower(),
            error_handling="handles" in review_content.lower() or "edge" in review_content.lower(),
            issues=extract_issues(review_content),
            score=extract_score(review_content)
        )
        
        # Determine success
        is_successful = (
            review_criteria["spec_compliance"] and
            review_criteria["correctness"] and
            review_criteria["score"] >= 75.0 and
            len(review_criteria["issues"]) == 0
        )
    
    # Update state
    state["messages"].append({
        "role": "reviewer",
        "content": review_content,
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "node": "reviewer",
            "score": review_criteria["score"],
            "issues": len(review_criteria["issues"])
        }
    })
    
    state["review_feedback"] = review_content
    state["spec_compliance_score"] = review_criteria["score"] / 100.0
    state["validation_errors"].extend(review_criteria["issues"])
    state["success"] = is_successful
    
    # Save successful implementations to memory for future learning
    if state["spec_compliance_score"] > 0.8 and state.get("code"):
        memory_saved = save_to_memory(
            task_description=state["task_description"],
            technical_spec=state["technical_spec"],
            final_code=state["code"],
            spec_compliance_score=state["spec_compliance_score"],
            task_id=state["task_id"]
        )
        if memory_saved:
            logger.info(f"Saved successful implementation to memory: {state['task_id']}")
    
    if is_successful:
        state["final_code"] = state["code"]
        state["status"] = "completed"
        logger.info(f"Review passed! Score: {review_criteria['score']:.1f}/100")
    else:
        state["status"] = "reviewing"
        logger.warning(
            f"Review failed. Score: {review_criteria['score']:.1f}/100, "
            f"Issues: {len(review_criteria['issues'])}"
        )
    
    state["last_updated"] = datetime.now().isoformat()
    
    return state


def extract_score(text: str) -> float:
    """Extract numeric score from review text."""
    import re
    match = re.search(r'(\d{1,3})\s*(?:/\s*100|%)', text)
    if match:
        return float(match.group(1))
    return 50.0  # Default if not found


def extract_issues(text: str) -> list[str]:
    """Extract issues from review text."""
    issues = []
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        if 'issue' in line.lower() or 'problem' in line.lower() or 'error' in line.lower():
            if i + 1 < len(lines):
                issues.append(lines[i + 1].strip())
    
    return issues[:5]  # Limit to top 5 issues
