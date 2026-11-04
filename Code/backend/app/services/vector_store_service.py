from sqlalchemy import text
from app.database import get_db_connection

def store_document_chunks(document_id:int , chunks:list[dict]):
    if not chunks:
        raise ValueError("No chunks provided for storage")
    query=text("""
        INSERT INTO document_chunks (
            document_id,
            chunk_index,
            page_number,
            content,
            embedding
        )
        VALUES (
            :document_id,
            :chunk_index,
            :page_number,
            :content,
            CAST(:embedding AS vector)
        )
    """)
    with get_db_connection() as connection:
        for chunk in chunks:
            connection.execute(
                query,{
                    "document_id": document_id,
                    "chunk_index": chunk["chunk_index"],
                    "page_number": chunk.get("page_number"),
                    "content": chunk["text"],
                    "embedding": str(chunk["embedding"])                    
                }
            )

def search_similar_chunks(document_id: int, query_embedding: list,limit: int = 5):
    if not query_embedding:
        raise ValueError("Query embedding is required")
    if limit <=0:
        raise ValueError("Limit must be greater than 0")


    query = text("""
        SELECT
            id,
            document_id,
            chunk_index,
            page_number,
            content,
            1 - (
                embedding <=> CAST(:query_embedding AS vector)
            ) AS similarity

        FROM document_chunks

        WHERE document_id = :document_id

        ORDER BY embedding <=> CAST(:query_embedding AS vector)

        LIMIT :limit
    """)
    with get_db_connection() as connection:
        result=connection.execute(query,{
            "document_id": document_id,
            "query_embedding": str(query_embedding),
            "limit": limit
        })
        chunks=result.mappings().all()
    response=[]
    for chunk in chunks:
        response.append(dict(chunk))    
    return response    