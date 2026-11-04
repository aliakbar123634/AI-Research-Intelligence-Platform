
import os
import time
import logging
from urllib.parse import urlparse

from tavily import TavilyClient
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

logger = logging.getLogger(__name__)

MAX_QUERY_LENGTH = 1000
MAX_RESULTS = 5
MAX_RETRIES = 3

def validate_search_query(query: str):

    if not isinstance(query, str):
        raise HTTPException(
            status_code=422,
            detail="Invalid search query"
        )

    query = query.strip()

    if not query or len(query) > MAX_QUERY_LENGTH:
        raise HTTPException(
            status_code=422,
            detail="Search query must be between 1 and 1000 characters"
        )

    if not any(char.isalnum() for char in query):
        raise HTTPException(
            status_code=422,
            detail="Search query must contain meaningful text"
        )

    return query

def validate_source_url(url: str) -> bool:

    try:
        parsed_url = urlparse(url)

        return (
            parsed_url.scheme == "https"
            and bool(parsed_url.hostname)
            and not parsed_url.username
            and not parsed_url.password
        )

    except (ValueError, AttributeError):
        return False

def search_web(query: str) -> list[dict]:

    query = validate_search_query(query)

    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        logger.error("Tavily API key is not configured")

        raise HTTPException(
            status_code=500,
            detail="Search service is not configured"
        )

    client = TavilyClient(api_key=api_key)

    last_error = None

    for attempt in range(MAX_RETRIES):

        try:
            response = client.search(
                query=query,
                max_results=MAX_RESULTS,
                search_depth="basic",
                timeout=15
            )

            results = []

            for item in response.get("results", []):

                url = item.get("url", "")

                if not validate_source_url(url):
                    continue

                results.append({
                    "title": item.get("title"),
                    "url": url,
                    "content": item.get("content"),
                    "score": item.get("score")
                })

            logger.info(
                "Tavily search completed. Results: %s",
                len(results)
            )

            return results

        except Exception as e:

            last_error = e

            logger.warning(
                "Tavily search attempt %s failed: %s",
                attempt + 1,
                type(e).__name__
            )

            if attempt < MAX_RETRIES - 1:
                time.sleep(attempt + 1)

    logger.error("Tavily search failed after retries")

    raise HTTPException(
        status_code=502,
        detail="Web search failed after retries"
    ) from last_error    