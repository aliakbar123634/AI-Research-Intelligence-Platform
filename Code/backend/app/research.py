from sqlalchemy import text
from pydantic import BaseModel , Field , ConfigDict , field_validator
from fastapi import APIRouter
from  .database import get_db_connection
from enum import Enum
from fastapi import HTTPException , UploadFile, File
from fastapi import Query
from .auth import get_current_user
from fastapi import Depends
from typing import Any
import json
from datetime import datetime, timezone
from app.services.research_service import *
from app.services.web_search_service import *
from app.services.llm_workflow import run_llm_workflow
from app.services.document_service import *
from app.services.document_processing_service import process_document
from pathlib import Path


router=APIRouter()

class ResearchRequest(BaseModel):
    query: str = Field(
        max_length=1000,
        min_length=1,
        description="Research question"
    )
    model_config=ConfigDict(
        str_strip_whitespace=True,
        extra="forbid"
    )
    @field_validator("query")
    @classmethod
    def validate_query(cls , value:str) -> str:
        if not value:
            raise ValueError("Research query cannot be empty")
        if not any(char.isalnum() for char in value):
            raise ValueError("Research query must contain meaningful text")
        return value


@router.post("/research")
def research(
    request: ResearchRequest,
    current_user: dict = Depends(get_current_user)
):
    insert_query = text("""
        INSERT INTO researches (question, status, user_id)
        VALUES (:question, 'pending', :user_id)
        RETURNING id, user_id, question, status, created_at
    """)

    try:
        with get_db_connection() as connection:
            result = connection.execute(insert_query, {
                "question": request.query,
                "user_id": current_user["id"]
            })

            research_record = dict(result.mappings().one())

    except Exception as e:
        print(f"Error creating research: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create research"
        )

    research_id = research_record["id"]
    user_id = current_user["id"]

    try:
        # Tavily search + Groq/LangGraph report generation
        workflow_result = run_llm_workflow(request.query)

        # Save the final report and mark research completed
        saved_research = save_research_result(
            research_id=research_id,
            user_id=user_id,
            answer=workflow_result["answer"],
            sources=workflow_result["sources"]
        )

        return {
            "message": "Research completed successfully",
            "research": saved_research
        }

    except Exception as e:
        print(f"Research workflow error: {e}")

        try:
            update_research_status(
                research_id=research_id,
                user_id=user_id,
                status="failed",
                error_message=str(e)[:1000]
            )
        except Exception as status_error:
            print(f"Failed to update research status: {status_error}")

        raise HTTPException(
            status_code=500,
            detail=f"Research workflow failed for research ID {research_id}"
        )



@router.get("/researches")
def get_researches(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    offset = (page - 1) * page_size

    count_query = text("""
        SELECT COUNT(*)
        FROM researches
        WHERE user_id = :user_id
    """)

    data_query = text("""
        SELECT
            id,
            user_id,
            question,
            status,
            result,
            error_message,
            created_at,
            updated_at,
            completed_at
        FROM researches
        WHERE user_id = :user_id
        ORDER BY id DESC
        LIMIT :page_size OFFSET :offset
    """)

    try:
        with get_db_connection() as connection:
            total = connection.execute(
                count_query,
                {"user_id": current_user["id"]}
            ).scalar_one()

            result = connection.execute(
                data_query,
                {
                    "user_id": current_user["id"],
                    "page_size": page_size,
                    "offset": offset
                }
            )

            researches = [
                dict(row) for row in result.mappings().all()
            ]

            return {
                "count": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "researches": researches
            }

    except Exception as e:
        print(f"Error fetching researches: {e}")
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch research records"
        )

@router.get("/researches/{research_id}")
def get_research(research_id:int , current_user: dict = Depends(get_current_user)):
    return get_research_by_id(
        research_id=research_id,
        user_id=current_user["id"]        
    )
      
class ResearchStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"            

class ResearchUpdateRequest(BaseModel):
    status: ResearchStatus = Field(
        description="Updated research status"
    )
    result: dict[str, Any] | None = None
    error_message: str | None = None
    model_config = ConfigDict(extra="forbid")

@router.patch("/researches/{research_id}")
async def update_research(research_id:int, request:ResearchUpdateRequest , current_user: dict = Depends(get_current_user)):
    return update_research_status(
        research_id=research_id,
        user_id=current_user["id"],
        status=request.status.value
    )    
                           
@router.delete("/researches/{research_id}")
def delete_research(research_id:int , current_user: dict = Depends(get_current_user)):
    DELETE_QUERY=text("""
    DELETE FROM researches 
    WHERE id=:research_id  
        AND user_id = :user_id
    RETURNING id  
""") 
    try:
        with get_db_connection() as connection:
            result=connection.execute(DELETE_QUERY, {"research_id":research_id ,  "user_id": current_user["id"]})
            if result.rowcount==0:
                return {"message":f"Research with id {research_id} not found"}
            return {"message":f"Research with id {research_id} deleted successfully"}   
    except Exception as e:
        print(f"Error occured: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while deleting the research record"
        ) 
    

def save_research_result(
    research_id: int,
    user_id: int,
    answer: str,
    sources: list[dict]        
)    :
    query=text("""
        UPDATE researches
        SET result = CAST(:result AS JSONB),
            status = 'completed',
            updated_at = NOW(),
            completed_at = NOW(),
            error_message = NULL
        WHERE id = :research_id
          AND user_id = :user_id
        RETURNING id, status, result, updated_at, completed_at    
    """)
    try:
        report={
            "answer":answer,
            "sources":sources
        }
        with get_db_connection() as connection:
            result=connection.execute(query,{
                "result": json.dumps(report),
                "research_id": research_id,
                "user_id": user_id                
            })
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
        print(f"Error saving research result: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to save research result"
        )   


@router.post("/researches/{research_id}/documents")
async def upload_research_document(
    research_id: int,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    # 1. Verify research ownership
    research = get_research_by_id(
        research_id=research_id,
        user_id=current_user["id"]
    )

    if not research:
        raise HTTPException(
            status_code=404,
            detail="Research not found"
        )

    # 2. Validate and save document
    document = await validate_and_save_documents(file)

    # 3. Save document metadata
    insert_query = text("""
        INSERT INTO research_documents (
            research_id,
            user_id,
            original_filename,
            stored_filename,
            file_path,
            file_type,
            file_size
        )
        VALUES (
            :research_id,
            :user_id,
            :original_filename,
            :stored_filename,
            :file_path,
            :file_type,
            :file_size
        )
        RETURNING id, research_id, original_filename,
                  file_type, file_size, status, created_at
    """)

    try:
        with get_db_connection() as connection:
            result = connection.execute(
                insert_query,
                {
                    "research_id": research_id,
                    "user_id": current_user["id"],
                    **document
                }
            )
            saved_document = dict( result.mappings().one())

        print("DOCUMENT SAVED:", saved_document["id"])

    # STEP 2: Process document
        print("STARTING DOCUMENT PROCESSING")

        processing_result = process_document(
            document_id=saved_document["id"],
            file_path=Path(document["file_path"])
        )

        print("PROCESSING RESULT:", processing_result)  

        return {
            "message": "Document uploaded successfully",
            "document": saved_document
        }

    except Exception as e:
        # Remove stored file if database insertion fails

        Path(document["file_path"]).unlink(missing_ok=True)

        print(f"Document metadata save error: {e}")

        raise HTTPException(
            status_code=500,
            detail="Failed to save document metadata"
        )

@router.get("/researches/{research_id}/documents")
async def list_research_documents(
    research_id:int,
    current_user:dict=Depends(get_current_user)
)  :
    research=get_research_by_id(
        research_id=research_id,
        user_id=current_user["id"]
    )
    if not research:
        raise HTTPException(
            status_code=404,
            detail="Research not found"
        )
    query=text("""
        SELECT id, research_id, original_filename, file_type, file_size, status, created_at
        FROM research_documents
        WHERE research_id=:research_id
        AND user_id=:user_id
        ORDER BY created_at DESC
    """)  
    try:
        with get_db_connection() as connection:
            result=connection.execute(query,{
                "research_id":research_id,
                "user_id":current_user["id"]
            })
            documents=[]
            rows = result.mappings().all()
            for row in rows:
                documents.append(dict(row))
        return{
            "documents": documents,
            "count":len(documents)
        } 
    except Exception as e:
        print(f"Error fetching documnents: {e}")
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch research documents"
        )       

@router.get("/researches/{research_id}/documents/{document_id}")
async def get_research_document(
    research_id:int,
    document_id:int,
    current_user:dict=Depends(get_current_user)
):
    research=get_research_by_id(
        research_id=research_id,
        user_id=current_user["id"]
    )
    if not research:
        raise HTTPException(
            status_code=404,
            detail="Research not found"
        )
    query=text("""
        SELECT *
        FROM research_documents
        WHERE id=:document_id
        AND user_id=:user_id
        AND research_id=:research_id
    """)
    try:
        with get_db_connection() as connection:
            result=connection.execute(query,{
                "document_id":document_id,
                "user_id":current_user["id"],
                "research_id":research_id
            })
            document= result.mappings().one_or_none()
            if not document:
                raise HTTPException(
                    status_code=404,
                    detail="Document not found"
                )
        return {
            "document": dict(document),
            "message": "Document retrieved successfully"
        }    
    except Exception as e:
        print(f"Error fetching document: {e}")
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch research document"
        )

@router.delete("/researches/{research_id}/documents/{document_id}")
async def delete_research_document(
    research_id:int,
    document_id:int,
    current_user:dict=Depends(get_current_user)
):
    research=get_research_by_id(
        research_id=research_id,
        user_id=current_user["id"]
    )
    if not research:
        raise HTTPException(
            status_code=404,
            detail="Research not found"
        )
    query=text("""
        DELETE FROM research_documents
        WHERE id=:document_id
        AND user_id=:user_id
        AND research_id=:research_id
        RETURNING file_path""")
    try:
        with get_db_connection() as connection:
            result=connection.execute(query,{
                "document_id":document_id,
                "user_id":current_user["id"],
                "research_id":research_id
            })
            deleted_document=result.mappings().one_or_none()
            if not deleted_document:
                raise HTTPException(
                    status_code=404,
                    detail="Document not found"
                )
            #Remove file from storage
        from pathlib import Path
        Path(deleted_document["file_path"]).unlink(missing_ok=True)
        return {
            "message":"Document deleted successfully",
        }
    except Exception as e:
        print(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=500,
            detail="Unable to delete research document"
        )