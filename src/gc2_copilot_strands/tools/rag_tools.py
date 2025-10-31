"""RAG tools for querying ChromaDB vector store."""

from strands import tool
from ..config import Config


@tool
def query_rag_context(user_request: str) -> str:
    """
    Query the RAG system for relevant context to help with pipeline planning.

    This tool searches multiple ChromaDB collections for context relevant to the user's request:
    - gc2_connectivity: Connection patterns between resources
    - gc2_templates: Example pipeline templates
    - gc2_guide: Configuration guides and best practices
    - gc2_schemas: Schema definitions and constraints

    Args:
        user_request: The user's natural language request describing the pipeline

    Returns:
        Formatted context string with relevant information from the vector store
    """
    chroma_client = Config.get_chroma_client()
    context_parts = []

    try:
        # Query connectivity patterns
        connectivity_results = chroma_client.query_collection(
            collection_name="gc2_connectivity",
            query_text=user_request,
            n_results=3
        )

        if connectivity_results and connectivity_results.get("documents"):
            context_parts.append("CONNECTIVITY PATTERNS:")
            for doc in connectivity_results["documents"][0][:2]:
                context_parts.append(f"- {doc}")

        # Query template examples
        template_results = chroma_client.query_collection(
            collection_name="gc2_templates",
            query_text=user_request,
            n_results=3
        )

        if template_results and template_results.get("documents"):
            context_parts.append("\nTEMPLATE EXAMPLES:")
            for doc in template_results["documents"][0][:2]:
                context_parts.append(f"- {doc}")

        # Query configuration guides
        guide_results = chroma_client.query_collection(
            collection_name="gc2_guide",
            query_text=user_request,
            n_results=2
        )

        if guide_results and guide_results.get("documents"):
            context_parts.append("\nCONFIGURATION GUIDANCE:")
            for doc in guide_results["documents"][0][:1]:
                context_parts.append(f"- {doc}")

        # Query schema definitions
        schema_results = chroma_client.query_collection(
            collection_name="gc2_schemas",
            query_text=user_request,
            n_results=2
        )

        if schema_results and schema_results.get("documents"):
            context_parts.append("\nSCHEMA DEFINITIONS:")
            for doc in schema_results["documents"][0][:1]:
                context_parts.append(f"- {doc}")

    except Exception as e:
        return f"Warning: Could not retrieve RAG context: {e}"

    return "\n".join(context_parts) if context_parts else "No relevant context found."
