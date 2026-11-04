from app.services.document_service import extract_document_text , clean_extracted_text , chunk_text
from app.services.embedding_service import generate_embedding
from app.services.vector_store_service import store_document_chunks
from pathlib import Path
from fastapi import HTTPException

def process_document(document_id:int , file_path:Path):
    try:
        file_extension = file_path.suffix.lower()
        extracted_document=extract_document_text(file_path , file_extension)
        clean_text=clean_extracted_text(extracted_document)
        chunks=chunk_text(clean_text)
        embedded_chunks=generate_embedding(chunks)
        store_document_chunks(
            document_id=document_id,
            chunks=embedded_chunks            
        )
        return {
            "document_id": document_id,
            "status": "processed",
            "chunks_created": len(embedded_chunks)
        }
    except HTTPException:
        raise


    except Exception as e:

        print(f"Document processing failed: {e}")

        raise HTTPException(
            status_code=500,
            detail="Document processing failed"
        )    