from .embedding_service import generate_query_embedding
from .vector_store_service import search_similar_chunks
from fastapi import HTTPException



def retrieve_relevant_chunks(query: str, document_id: int, limit: int = 5):
    try:    
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if limit <= 0:
            raise ValueError("limit cannot be zero or less than zero")
        query_embedding=generate_query_embedding(query)
        chunks=search_similar_chunks(document_id=document_id,  query_embedding=query_embedding , limit=limit )
        if not chunks:
            return{
                "query": query,
                "chunks_found": 0,
                "chunks": []
            }
        return {
            "query": query,
            "chunks_found": len(chunks),
            "chunks": chunks
        }
    except HTTPException:
        raise

    except Exception as e:
        print(f"Retrieval error: {e}")

        raise HTTPException(
            status_code=500,
            detail="Error retrieving relevant document chunks"
        )    