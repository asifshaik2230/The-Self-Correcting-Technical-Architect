import logging
import re
from e2b_code_interpreter import Sandbox
from src.state import AgentState, ExecutionResult
from src.config import settings

logger = logging.getLogger(__name__)

def executor_node(state: AgentState) -> dict:
    """
    Executor node: Executes core code and tests in the SAME sandbox session.
    
    This node:
    1. Creates a sandbox environment
    2. Runs the generated core implementation code (functions remain in memory)
    3. Runs the generated test suite in SAME session (tests can call core functions)
    4. Captures exact error details for failed tests
    5. Returns execution results for reviewer analysis
    
    Args:
        state: Current agent state with code and tests
        
    Returns:
        dict: Updated execution state with detailed test failure info
    """
    logger.info("Executor node: Executing code and tests in sandbox...")
    
    core_code = state.get("code", "")
    test_code = state.get("test_code", "")
    
    if not core_code:
        logger.error("No core code to execute")
        return {"status": "reviewing", "last_execution": {"success": False, "stderr": "No code to execute"}}
    
    try:
        with Sandbox.create(api_key=settings.e2b_api_key) as sandbox:
            # Step 1: Execute core implementation code (to load functions into memory)
            logger.info("Running core implementation...")
            core_execution = sandbox.run_code(core_code, timeout=settings.code_execution_timeout)
            
            # Parse core execution results
            core_logs = getattr(core_execution, 'logs', None)
            core_stdout = _extract_output(core_logs, 'stdout') if core_logs else ""
            core_stderr = _extract_output(core_logs, 'stderr') if core_logs else ""
            core_error = getattr(core_execution, 'error', None)
            
            core_success = core_error is None
            core_result = ExecutionResult(
                success=core_success,
                stdout=core_stdout,
                stderr=core_stderr,
                execution_time=0.5,
                artifacts={}
            )
            
            # Step 2: Execute test suite in SAME sandbox session
            # This way, test code can access functions defined in core_code
            test_result = None
            test_success = False
            
            if test_code:
                logger.info("Running test suite in same sandbox session...")
                
                # Run ONLY the test code (core functions are already in memory from Step 1)
                # Do NOT combine - we already loaded the core functions
                test_execution = sandbox.run_code(test_code, timeout=settings.code_execution_timeout)
                
                # Parse test execution results
                test_logs = getattr(test_execution, 'logs', None)
                test_stdout = _extract_output(test_logs, 'stdout') if test_logs else ""
                test_stderr = _extract_output(test_logs, 'stderr') if test_logs else ""
                test_error = getattr(test_execution, 'error', None)
                
                # Determine if tests passed by looking for pass indicators
                # and absence of fail indicators
                has_fail_marker = "✗" in test_stdout or "FAILED" in test_stdout or "failed" in test_stdout.lower()
                has_pass_marker = "✓" in test_stdout or "passed" in test_stdout.lower()
                
                # Tests pass if: has pass markers, no fail markers, no errors
                test_success = has_pass_marker and not has_fail_marker and test_error is None
                
                # Capture detailed failure info for reviewer
                failure_details = ""
                if test_stderr:
                    failure_details = f"STDERR: {test_stderr}"
                if has_fail_marker and test_stdout:
                    # Extract failure messages from stdout
                    failure_details = f"TEST FAILURES:\n{test_stdout}"
                
                test_result = ExecutionResult(
                    success=test_success,
                    stdout=test_stdout,
                    stderr=failure_details if failure_details else "",
                    execution_time=0.5,
                    artifacts={
                        "test_summary": {
                            "has_passes": has_pass_marker,
                            "has_failures": has_fail_marker,
                            "has_error": test_error is not None,
                            "error_details": test_error
                        }
                    }
                )
                
                logger.info(f"Tests: Passed={has_pass_marker}, Failed={has_fail_marker}, Error={test_error is not None}, Success={test_success}")
                logger.debug(f"Test stdout:\n{test_stdout[:500]}")
                if test_stderr:
                    logger.debug(f"Test stderr:\n{test_stderr[:500]}")
            
            # Step 3: Combine results
            combined_stdout = core_stdout
            combined_stderr = core_stderr
            combined_success = core_success and (test_success if test_result else True)
            
            if test_result:
                combined_stdout += "\n\n=== TEST RESULTS ===\n" + test_result["stdout"]
                if test_result["stderr"]:
                    combined_stderr += "\n\n=== TEST FAILURES ===\n" + test_result["stderr"]
            
            final_result = ExecutionResult(
                success=combined_success,
                stdout=combined_stdout,
                stderr=combined_stderr,
                execution_time=1.0,
                artifacts={
                    "core_execution": core_result,
                    "test_execution": test_result
                }
            )
            
            logger.info(f"Execution completed - Core: {core_success}, Tests: {test_success if test_result else 'N/A'}")
            
            return {
                "last_execution": final_result,
                "execution_logs": state.get("execution_logs", []) + [final_result],
                "status": "reviewing"
            }
            
    except Exception as e:
        logger.error(f"Sandbox execution error: {e}")
        error_result = ExecutionResult(
            success=False,
            stdout="",
            stderr=str(e),
            execution_time=0.0,
            artifacts={}
        )
        return {
            "last_execution": error_result,
            "execution_logs": state.get("execution_logs", []) + [error_result],
            "status": "reviewing"
        }


def _extract_output(logs, output_type: str) -> str:
    """Extract stdout/stderr from execution logs."""
    if not logs:
        return ""
    
    output = getattr(logs, output_type, "")
    if isinstance(output, list):
        return "".join(output)
    return str(output)