"""
Researcher Node: Analyzes task requirements, performs web research, and generates a plan.
"""

import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from src.state import AgentState
from src.config import settings
from src.tools.search import perform_web_search
from src.tools.memory import search_memory

logger = logging.getLogger(__name__)


def researcher_node(state: AgentState) -> AgentState:
    """
    Researcher node: Analyzes task requirements, searches memory, performs web research, and creates a plan.
    
    This node:
    1. Reviews the task description and technical specification
    2. Searches long-term memory for relevant historical solutions
    3. Generates a specific search query for web research (if needed)
    4. Performs web search using Tavily API
    5. Incorporates both memory and search results into the analysis
    6. Generates a research-grounded implementation plan
    
    Args:
        state: Current agent state
        
    Returns:
        AgentState: Updated state with research findings and plan
    """
    logger.info("Researcher node: Analyzing task requirements...")
    
    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.7
    )
    
    # Step 1: Search memory for relevant historical solutions
    memory_results = search_memory(state['task_description'], min_score=0.8, max_results=2)
    state["memory_hits"] = memory_results
    
    logger.info(f"Found {len(memory_results)} relevant memory entries")
    
    # Step 2: Generate a specific search query (if we have memory results, we might need less web search)
    query_prompt = f"""Based on this task, generate a specific web search query to find relevant technical information.

Task: {state['task_description']}

Technical Specification:
{state['technical_spec']}

Generate a concise, specific search query that would help find:
- Best practices and patterns for this type of implementation
- Technical documentation or examples
- Recent developments or libraries that could be relevant

Return only the search query, nothing else."""

    query_response = llm.invoke([HumanMessage(content=query_prompt)])
    search_query = query_response.content.strip()
    
    logger.info(f"Generated search query: {search_query}")
    
    # Step 3: Perform web search
    search_results = perform_web_search(search_query, max_results=3)
    
    # Step 4: Store search results in state
    state["research_notes"] = search_results
    
    # Step 5: Create comprehensive research prompt with both memory and web results
    memory_section = ""
    if memory_results:
        memory_context = ""
        for result in memory_results:
            score = result.get('score', result.get('spec_compliance_score', 0.0))
            code_text = result.get('code', result.get('final_code', ''))
            memory_context += f"Previous Solution (Score: {score:.1f}):\n{code_text[:1000]}{'...' if len(code_text) > 1000 else ''}\n\n"
        memory_section = "\nHistoric Reference Code:\n" + memory_context
    
    research_prompt = f"""You are an expert technical architect. Analyze the following task and specification, incorporating both historical solutions and current web search results.

Task: {state['task_description']}

Technical Specification:
{state['technical_spec']}{memory_section}

Web Search Results:
{search_results}

Provide a detailed, research-grounded implementation plan that includes:
1. Key components and modules needed (based on research findings and historical solutions)
2. Algorithm or approach to use (considering current best practices and proven patterns)
3. Potential challenges and solutions (informed by search results and past experiences)
4. Implementation steps with specific technical details
5. Testing strategy
6. Any relevant libraries, frameworks, or tools identified from research

Be thorough but concise, and explicitly reference findings from both the search results and historical solutions where relevant."""
    
    # Get analysis from LLM
    response = llm.invoke([HumanMessage(content=research_prompt)])
    research_content = response.content
    
    # Update state with research findings
    state["messages"].append({
        "role": "assistant",
        "content": research_content,
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "metadata": {
            "node": "researcher",
            "search_query": search_query,
            "memory_hits": len(memory_results),
            "search_results_summary": search_results[:500] + "..." if len(search_results) > 500 else search_results
        }
    })
    
    state["status"] = "coding"
    state["last_updated"] = __import__("datetime").datetime.now().isoformat()
    
    logger.info("Researcher node: Research-grounded plan generated successfully")
    
    return state
