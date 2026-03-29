import logging
import re
from e2b_code_interpreter import Sandbox
from src.state import AgentState, ExecutionResult
from src.config import settings

logger = logging.getLogger(__name__)

def executor_node(state: AgentState) -> dict:
    """
    Executor node: Executes both core code and comprehensive test suite in sandbox.
    
    This node:
    1. Runs the generated core implementation code
    2. Runs the generated test suite against the implementation
    3. Combines results for comprehensive validation
    4. Returns execution results for reviewer analysis
    
    Args:
        state: Current agent state with code and tests
        
    Returns:
        dict: Updated execution state
    """
    logger.info("Executor node: Executing code and tests in sandbox...")
    
    core_code = state.get("code", "")
    test_code = state.get("test_code", "")
    
    if not core_code:
        logger.error("No core code to execute")
        return {"status": "reviewing", "last_execution": {"success": False, "stderr": "No code to execute"}}
    
    try:
        with Sandbox.create(api_key=settings.e2b_api_key) as sandbox:
            # Step 1: Execute core implementation code
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
            
            # Step 2: Execute test suite (if available)
            test_result = None
            if test_code:
                logger.info("Running test suite...")
                # Combine core code and test code for execution
                combined_code = core_code + "\n\n" + test_code
                test_execution = sandbox.run_code(combined_code, timeout=settings.code_execution_timeout)
                
                # Parse test execution results
                test_logs = getattr(test_execution, 'logs', None)
                test_stdout = _extract_output(test_logs, 'stdout') if test_logs else ""
                test_stderr = _extract_output(test_logs, 'stderr') if test_logs else ""
                test_error = getattr(test_execution, 'error', None)
                
                test_success = test_error is None and "FAILED" not in test_stdout and "ERROR" not in test_stderr
                test_result = ExecutionResult(
                    success=test_success,
                    stdout=test_stdout,
                    stderr=test_stderr,
                    execution_time=0.5,
                    artifacts={}
                )
            
            # Step 3: Combine results
            combined_stdout = core_stdout
            combined_stderr = core_stderr
            combined_success = core_success
            
            if test_result:
                combined_stdout += "\n\n=== TEST RESULTS ===\n" + test_result["stdout"]
                if test_result["stderr"]:
                    combined_stderr += "\n\n=== TEST ERRORS ===\n" + test_result["stderr"]
                # Tests are critical - if they fail, overall success is false
                combined_success = combined_success and test_result["success"]
            
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
            
            logger.info(f"Execution completed - Core: {core_success}, Tests: {test_result['success'] if test_result else 'N/A'}")
            
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