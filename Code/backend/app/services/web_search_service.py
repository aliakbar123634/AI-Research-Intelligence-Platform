import os
from tavily import TavilyClient
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

def search_web(query: str) -> list[dict]:
    api_key=os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Tavily API key is not configured"            
        )
    try:
        client = TavilyClient(api_key=api_key)
        response=client.search(
            query=query,
            max_results=5,
            search_depth="basic"            
        )
        return [
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "content": item.get("content"),
                "score": item.get("score")
            }
            for item in response.get("results", [])
        ]        
    except Exception as e:
        print(f"Tavily search error: {e}")
        raise HTTPException(
            status_code=502,
            detail="Web search failed"
        )    