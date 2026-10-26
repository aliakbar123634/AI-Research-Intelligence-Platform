from sqlalchemy import text
from fastapi import HTTPException
from app.database import get_db_connection


def get_research_by_id(research_id: int, user_id: int):
    query=text("""
    SELECT * FROM researches
    WHERE id = :research_id
        AND user_id = :user_id
""")
    try:
        with get_db_connection() as connection:
            result=connection.execute(
                query,{
                "research_id": research_id,
                "user_id": user_id
                }
            )
            research=result.mappings().one_or_none()
            if research is None:
                raise HTTPException(
                    status_code=404,
                    detail="Research not found"
                )
            return dict(research)    
    except HTTPException:
        raise                
    except Exception as e:
        print(f"Error fetching research: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch research"
        )    



def update_research_status(
    research_id: int,
    user_id: int,
    status: str
):
    query = text("""
    UPDATE researches
    SET status = CAST(:status AS VARCHAR),
        updated_at = NOW(),
        completed_at = CASE
            WHEN CAST(:status AS VARCHAR) IN ('completed', 'failed')
            THEN NOW()
            ELSE NULL
        END
    WHERE id = :research_id
      AND user_id = :user_id
    RETURNING id, status, updated_at, completed_at
""")

    try:
        with get_db_connection() as connection:
            result = connection.execute(query, {
                "research_id": research_id,
                "user_id": user_id,
                "status": status
            })

            research = result.mappings().one_or_none()

            if research is None:
                raise HTTPException(
                    status_code=404,
                    detail="Research not found"
                )

            return dict(research)

    except HTTPException:
        raise

    except Exception as e:
        print(f"Error updating research status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update research status"
        ) 

def save_research_sources(
    research_id: int,
    sources: list[dict]
):
    query=text("""
    INSERT INTO research_sources
        (research_id, title, url, content, score)
    VALUES
        (:research_id, :title, :url, :content, :score)     
    """) 
    try:
        with get_db_connection() as connection:
            for source in sources:
                print("PROCESSING SOURCE:", source)

                if not source.get("url"):
                    print("SKIPPED: URL missing")
                    continue
                connection.execute(query,{
                    "research_id": research_id,
                    "title": source.get("title"),
                    "url": source["url"],
                    "content": source.get("content"),
                    "score": source.get("score")
                })    
        return len(sources)
    except Exception as e:
        print(f"Error saving research sources: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to save research sources"
        )                        