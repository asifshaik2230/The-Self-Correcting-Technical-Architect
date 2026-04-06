"""
Streamlit UI for the Self-Correcting Technical Architect Agent.

Provides interactive interface for code generation with real-time progress tracking.
"""

import asyncio
import streamlit as st
from datetime import datetime
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import run_agent


def main():
    st.set_page_config(
        page_title="Self-Correcting Technical Architect",
        page_icon="🏗️",
        layout="wide"
    )
    
    st.title("🏗️ Self-Correcting Technical Architect")
    st.markdown(
        "Generate production-ready code with automatic testing and refinement"
    )
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.subheader("Task Definition")
        task_description = st.text_area(
            "Task Description",
            placeholder="e.g., Write a Python function that calculates the Fibonacci sequence",
            height=100,
            key="task_desc"
        )
        
        st.subheader("Technical Specification")
        technical_spec = st.text_area(
            "Requirements & Constraints",
            placeholder="""e.g.:
1. Function should accept n as parameter
2. Should return list of first n Fibonacci numbers
3. Should handle edge cases (n <= 0)
4. Should use efficient algorithms""",
            height=150,
            key="tech_spec"
        )
        
        task_id = st.text_input(
            "Task ID (optional)",
            value=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            key="task_id"
        )
    
    with col2:
        st.subheader("Progress & Results")
        progress_placeholder = st.empty()
        status_placeholder = st.empty()
        result_placeholder = st.empty()
    
    if st.button("🚀 Generate Architecture & Code", use_container_width=True):
        if not task_description or not technical_spec:
            st.error("Please provide both Task Description and Technical Specification")
            return
        
        # Initialize progress tracking
        progress_placeholder.info("⏳ Initializing agent...")
        
        try:
            # Run the agent asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Update UI as execution progresses
            status_placeholder.info("🔍 Phase 1: Researching requirements...")
            final_state = loop.run_until_complete(
                run_agent(task_description, technical_spec, task_id)
            )
            
            if final_state["success"]:
                progress_placeholder.success("✅ Generation Completed Successfully!")
                
                # Display results
                with result_placeholder.container():
                    st.markdown("---")
                    
                    # Score and metadata
                    col_score, col_retry = st.columns(2)
                    with col_score:
                        score = final_state.get("spec_compliance_score", 0)
                        st.metric(
                            "Compliance Score",
                            f"{score:.1%}",
                            delta="High Confidence" if score > 0.9 else "Good"
                        )
                    with col_retry:
                        retries = final_state.get("retry_count", 0)
                        st.metric("Retry Attempts", retries)
                    
                    st.markdown("---")
                    
                    # Display code
                    st.subheader("Generated Code")
                    code_output = final_state.get("code", "")
                    st.code(code_output, language="python")
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Code",
                        data=code_output,
                        file_name=f"{task_id}.py",
                        mime="text/plain"
                    )
                    
                    # Display final report
                    if final_state.get("final_report"):
                        st.markdown("---")
                        st.subheader("Execution Report")
                        st.text(final_state["final_report"])
            else:
                progress_placeholder.error("❌ Generation Failed")
                status_placeholder.error(
                    f"Status: {final_state.get('status', 'unknown')}\n\n"
                    f"Feedback: {final_state.get('review_feedback', 'No feedback')}"
                )
        
        except Exception as e:
            progress_placeholder.error(f"❌ Error: {str(e)}")
            st.exception(e)
    
    # Sidebar info
    with st.sidebar:
        st.markdown("---")
        st.subheader("About")
        st.markdown(
            """
            **Self-Correcting Technical Architect V2**
            
            An AI-powered agent that:
            - 🔍 Researches requirements
            - 💻 Generates production code
            - 🧪 Creates comprehensive tests
            - 🔄 Refines iteratively
            - ✅ Validates against specs
            """
        )
        
        st.markdown("---")
        st.subheader("Architecture")
        st.markdown(
            """
            1. **Researcher** - Analyzes requirements
            2. **Coder** - Generates code + tests
            3. **Executor** - Runs in sandboxed E2B
            4. **Reviewer** - Validates & scores
            5. **Loop** - Refines until success
            """
        )


if __name__ == "__main__":
    main()
