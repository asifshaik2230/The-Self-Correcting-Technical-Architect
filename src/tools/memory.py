import chromadb
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Initialize ChromaDB persistent client locally
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="agent_memory")

def save_to_memory(
    task_description: str, 
    code: str = "",
    final_code: str = "",
    score: float = 100.0,  # Default to 100.0 if the Reviewer forgets to pass it
    technical_spec: str = "", 
    task_id: str = "",
    **kwargs
):
    """Saves high-scoring implementation details and metadata to the Vector DB."""
    try:
        # Safely handle whether the Reviewer passes 'code' or 'final_code'
        code_to_save = final_code if final_code else code
        if not code_to_save and "code" in kwargs:
            code_to_save = kwargs["code"]
            
        # Safely catch if the reviewer passed 'spec_compliance_score' instead
        final_score = kwargs.get("spec_compliance_score", score)

        # Use task_id if provided, otherwise generate a unique timestamp ID
        doc_id = task_id if task_id else f"mem_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        collection.add(
            documents=[task_description],
            metadatas=[{
                "code": code_to_save,
                "score": float(final_score),
                "technical_spec": technical_spec,
                "task_id": task_id,
                "timestamp": datetime.now().isoformat()
            }],
            ids=[doc_id]
        )
        logger.info(f"Saved successful implementation to memory: {doc_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to save to memory: {str(e)}")
        return False

def search_memory(query: str, min_score: float = 0.8, max_results: int = 2, **kwargs):
    """
    Returns previous similar tasks from the Vector DB.
    """
    try:
        if collection.count() == 0:
            return []
            
        results = collection.query(
            query_texts=[query],
            n_results=min(max_results, collection.count())
        )
        
        matches = []
        if results and 'metadatas' in results and results['metadatas']:
            if len(results['metadatas']) > 0 and results['metadatas'][0]:
                for meta in results['metadatas'][0]:
                    # Filter by the min_score threshold
                    # Handle both percentage (98.0) and decimal (0.98) scoring formats
                    meta_score = float(meta.get('score', 0.0))
                    normalized_score = meta_score if meta_score <= 1.0 else meta_score / 100.0
                    normalized_min = min_score if min_score <= 1.0 else min_score / 100.0
                    
                    if normalized_score >= normalized_min:
                        matches.append(meta)
                    
        return matches
    except Exception as e:
        logger.error(f"Memory search failed: {str(e)}")
        return []