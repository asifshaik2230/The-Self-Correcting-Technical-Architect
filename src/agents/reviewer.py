"""
Reviewer Node: Validates generated code against technical specifications.
"""

import logging
from datetime import datetime
from langchain_openai import ChatOpenAI
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
    
    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.3  # Lower temperature for objective review
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
            # Tests passed - high confidence success
            review_criteria = ReviewCriteria(
                correctness=True,
                spec_compliance=True,
                performance=True,
                readability=True,
                error_handling=True,
                issues=[],
                score=95.0
            )
            review_content = "✅ CODE PASSED ALL TESTS - HIGH CONFIDENCE APPROVAL\n\nTest-driven validation successful. All automated tests passed, indicating the implementation meets specifications and handles edge cases correctly."
            is_successful = True
        else:
            # Tests failed - analyze core execution to determine severity
            core_execution_success = False
            if state.get("last_execution") and state["last_execution"].get("artifacts"):
                core_exec = state["last_execution"]["artifacts"].get("core_execution")
                if core_exec and core_exec.get("success"):
                    core_execution_success = True
            
            if core_execution_success:
                # Core works but tests fail - partial credit, allow retry with feedback
                review_criteria = ReviewCriteria(
                    correctness=True,  # Core logic works
                    spec_compliance=False,  # But doesn't pass tests
                    performance=True,  # Assume OK if core works
                    readability=True,  # Assume OK
                    error_handling=False,  # Tests indicate issues
                    issues=["Tests failed but core execution succeeded - likely edge case or test logic issues"],
                    score=60.0  # Partial credit
                )
                review_content = "⚠️ PARTIAL SUCCESS - TESTS FAILED BUT CORE WORKS\n\nThe core implementation executes successfully, but automated tests are failing. This suggests the basic functionality works but there may be issues with edge cases, input validation, or test expectations. Recommend refining the implementation."
                is_successful = False  # Allow retry
            else:
                # Both core and tests failed - critical issues
                review_criteria = ReviewCriteria(
                    correctness=False,
                    spec_compliance=False,
                    performance=False,
                    readability=False,
                    error_handling=False,
                    issues=["Both core execution and tests failed - implementation has critical issues"],
                    score=20.0
                )
                review_content = "❌ CRITICAL FAILURE - CODE DOESN'T WORK\n\nBoth the core implementation and tests failed. The code has fundamental issues that prevent execution."
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
