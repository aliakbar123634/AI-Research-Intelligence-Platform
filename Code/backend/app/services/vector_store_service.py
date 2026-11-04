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