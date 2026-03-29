"""
Memory Tool: Long-term experience persistence for the agent.

Stores successful implementations and retrieves relevant historical solutions
to accelerate planning and improve code quality through learning from past successes.
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import threading
from pathlib import Path

from src.config import settings

logger = logging.getLogger(__name__)

# Thread lock for thread-safe JSON file operations
_memory_lock = threading.Lock()


class MemoryEntry:
    """Represents a stored memory entry."""

    def __init__(
        self,
        task_id: str,
        task_description: str,
        technical_spec: str,
        final_code: str,
        spec_compliance_score: float,
        timestamp: str,
        tags: Optional[List[str]] = None
    ):
        self.task_id = task_id
        self.task_description = task_description
        self.technical_spec = technical_spec
        self.final_code = final_code
        self.spec_compliance_score = spec_compliance_score
        self.timestamp = timestamp
        self.tags = tags or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "task_description": self.task_description,
            "technical_spec": self.technical_spec,
            "final_code": self.final_code,
            "spec_compliance_score": self.spec_compliance_score,
            "timestamp": self.timestamp,
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Create from dictionary."""
        return cls(
            task_id=data["task_id"],
            task_description=data["task_description"],
            technical_spec=data["technical_spec"],
            final_code=data["final_code"],
            spec_compliance_score=data["spec_compliance_score"],
            timestamp=data["timestamp"],
            tags=data.get("tags", [])
        )


def _ensure_memory_file() -> None:
    """Ensure the memory file and directory exist."""
    memory_path = Path(settings.memory_file_path)
    memory_path.parent.mkdir(parents=True, exist_ok=True)

    if not memory_path.exists():
        with open(memory_path, 'w') as f:
            json.dump([], f)
        logger.info(f"Created new memory file: {memory_path}")


def _load_memory() -> List[MemoryEntry]:
    """Load all memory entries from file."""
    try:
        with _memory_lock:
            _ensure_memory_file()
            with open(settings.memory_file_path, 'r') as f:
                data = json.load(f)
                return [MemoryEntry.from_dict(entry) for entry in data]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Error loading memory file: {e}")
        return []


def _save_memory(entries: List[MemoryEntry]) -> None:
    """Save all memory entries to file."""
    try:
        with _memory_lock:
            _ensure_memory_file()
            with open(settings.memory_file_path, 'w') as f:
                json.dump([entry.to_dict() for entry in entries], f, indent=2)
    except Exception as e:
        logger.error(f"Error saving memory file: {e}")


def save_to_memory(
    task_description: str,
    technical_spec: str,
    final_code: str,
    spec_compliance_score: float,
    task_id: str = None
) -> bool:
    """
    Save a successful implementation to long-term memory.

    Args:
        task_description: Description of the task
        technical_spec: Technical specification
        final_code: The final working code
        spec_compliance_score: Compliance score (0.0 to 1.0)
        task_id: Optional task identifier

    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        if spec_compliance_score < 0.8:
            logger.debug(f"Score {spec_compliance_score} too low for memory storage")
            return False

        # Generate tags from task description for better searchability
        tags = _generate_tags(task_description)

        entry = MemoryEntry(
            task_id=task_id or f"task_{int(datetime.now().timestamp())}",
            task_description=task_description,
            technical_spec=technical_spec,
            final_code=final_code,
            spec_compliance_score=spec_compliance_score,
            timestamp=datetime.now().isoformat(),
            tags=tags
        )

        # Load existing entries, add new one, save back
        entries = _load_memory()
        entries.append(entry)
        _save_memory(entries)

        logger.info(f"Saved successful implementation to memory: {task_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to save to memory: {e}")
        return False


def search_memory(query: str, min_score: float = 0.8, max_results: int = 3) -> List[Dict[str, Any]]:
    """
    Search memory for relevant historical implementations.

    Args:
        query: Search query (task description or keywords)
        min_score: Minimum compliance score to consider
        max_results: Maximum number of results to return

    Returns:
        List of matching memory entries with relevance scores
    """
    try:
        entries = _load_memory()

        # Filter by minimum score
        qualified_entries = [e for e in entries if e.spec_compliance_score >= min_score]

        if not qualified_entries:
            return []

        # Score entries by relevance to query
        scored_entries = []
        query_lower = query.lower()

        for entry in qualified_entries:
            relevance_score = _calculate_relevance(query_lower, entry)
            if relevance_score > 0:
                scored_entries.append({
                    "entry": entry,
                    "relevance_score": relevance_score
                })

        # Sort by relevance score (descending) and compliance score (descending)
        scored_entries.sort(
            key=lambda x: (x["relevance_score"], x["entry"].spec_compliance_score),
            reverse=True
        )

        # Return top results
        results = []
        for item in scored_entries[:max_results]:
            entry = item["entry"]
            results.append({
                "task_id": entry.task_id,
                "task_description": entry.task_description,
                "technical_spec": entry.technical_spec,
                "final_code": entry.final_code,
                "spec_compliance_score": entry.spec_compliance_score,
                "timestamp": entry.timestamp,
                "tags": entry.tags,
                "relevance_score": item["relevance_score"]
            })

        logger.info(f"Found {len(results)} relevant memory entries for query: {query}")
        return results

    except Exception as e:
        logger.error(f"Failed to search memory: {e}")
        return []


def _generate_tags(task_description: str) -> List[str]:
    """Generate tags from task description for better searchability."""
    # Simple keyword extraction - could be enhanced with NLP
    words = task_description.lower().split()
    tags = []

    # Common programming keywords
    keywords = [
        "function", "class", "method", "algorithm", "data", "structure",
        "api", "web", "file", "database", "array", "list", "dict", "string",
        "number", "math", "calculation", "sort", "search", "parse", "validate",
        "convert", "transform", "process", "handle", "error", "exception"
    ]

    for word in words:
        if word in keywords:
            tags.append(word)

    # Add the first few significant words
    significant_words = [w for w in words if len(w) > 3][:3]
    tags.extend(significant_words)

    return list(set(tags))  # Remove duplicates


def _calculate_relevance(query: str, entry: MemoryEntry) -> float:
    """
    Calculate relevance score between query and memory entry.

    Returns a score from 0.0 to 1.0 based on text similarity.
    """
    query_words = set(query.split())
    task_words = set(entry.task_description.lower().split())
    spec_words = set(entry.technical_spec.lower().split())
    tag_matches = set(entry.tags) & query_words

    # Calculate word overlap
    task_overlap = len(query_words & task_words) / len(query_words) if query_words else 0
    spec_overlap = len(query_words & spec_words) / len(query_words) if query_words else 0
    tag_overlap = len(tag_matches) / len(query_words) if query_words else 0

    # Weighted relevance score
    relevance = (task_overlap * 0.5) + (spec_overlap * 0.3) + (tag_overlap * 0.2)

    return min(relevance, 1.0)  # Cap at 1.0