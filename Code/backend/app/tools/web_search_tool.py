from langchain_core.tools import tool
from app.services.web_search_service import search_web

@tool
def web_search(query: str):
    """
    Search the web for up-to-date information relevant to a research query.

    Use this tool when external or current information is needed.
    """

    if not query or not query.strip():
        return {
            "error": "Search query cannot be empty"
        }

    try:
        results = search_web(query.strip())

        return results

    except Exception as e:
        return {
            "error": f"Web search failed: {str(e)}"
        }