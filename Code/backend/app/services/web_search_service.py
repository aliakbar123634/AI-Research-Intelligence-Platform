import os
import time 
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
    client = TavilyClient(api_key=api_key)
    last_error = None
    for attempt in range(3):
        try:
            response=client.search(
            query=query,
            max_results=5,
            search_depth="basic",
            timeout=15          
            )
            results=[]
            for item in response.get("results",[]):
                source={
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "content": item.get("content"),
                    "score": item.get("score")
                }
                results.append(source)
            return results    
            
      
        except Exception as e:
            last_error=e
            print(f"Tavily attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(1 * (attempt + 1))
        
    raise HTTPException(
        status_code=502,
        detail="Web search failed after retries"
    ) from last_error   