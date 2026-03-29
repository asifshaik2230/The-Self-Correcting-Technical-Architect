"""
Search Tool: Web search functionality using Tavily API.

Provides web search capabilities for the agent to gather external information
and research findings to inform implementation decisions.
"""

import logging
from typing import List, Dict, Any
from tavily import TavilyClient

from src.config import settings

logger = logging.getLogger(__name__)


def perform_web_search(query: str, max_results: int = 3) -> str:
    """
    Perform a web search using Tavily API and return formatted results.

    Args:
        query: The search query to execute
        max_results: Maximum number of results to return (default: 3)

    Returns:
        str: Formatted string containing the top search results
    """
    try:
        # Initialize Tavily client
        client = TavilyClient(api_key=settings.tavily_api_key)

        # Perform search
        logger.info(f"Performing web search for: {query}")
        response = client.search(query=query, max_results=max_results)

        # Format results
        formatted_results = _format_search_results(response)

        logger.info(f"Search completed successfully, found {len(response.get('results', []))} results")
        return formatted_results

    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return f"Search failed: {str(e)}"


def _format_search_results(response: Dict[str, Any]) -> str:
    """
    Format the Tavily search response into a readable string.

    Args:
        response: Raw response from Tavily API

    Returns:
        str: Formatted search results
    """
    results = response.get('results', [])

    if not results:
        return "No search results found."

    formatted = "Web Search Results:\n\n"

    for i, result in enumerate(results, 1):
        title = result.get('title', 'No title')
        url = result.get('url', 'No URL')
        content = result.get('content', 'No content')

        formatted += f"{i}. **{title}**\n"
        formatted += f"   URL: {url}\n"
        formatted += f"   Content: {content[:300]}{'...' if len(content) > 300 else ''}\n\n"

    return formatted