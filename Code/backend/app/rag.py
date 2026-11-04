from fastapi import APIRouter
from pydantic import BaseModel

from app.services.rag_service import generate_rag_answer

router=APIRouter()

class RAGQuestionRequest(BaseModel):
    question: str
    document_id: int
    limit: int = 5
@router.post("/ask")
def ask_document(request: RAGQuestionRequest):

    result = generate_rag_answer(
        question=request.question,
        document_id=request.document_id,
        limit=request.limit
    )

    return result        