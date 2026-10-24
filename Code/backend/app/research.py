from sqlalchemy import text
from pydantic import BaseModel , Field
from fastapi import APIRouter
from  .database import get_db_connection
from enum import Enum
from fastapi import HTTPException
from fastapi import Query
from .auth import get_current_user
from fastapi import Depends



router=APIRouter()

class ResearchRequest(BaseModel):
    query:str=Field(
        max_length=1000,
        min_length=1,
        description="Research question"
    )

@router.post("/research")
async def research(request:ResearchRequest , current_user:str=Depends(get_current_user)):
    INSERT_QUERY =text("""
        INSERT INTO researches (question, status , user_id)
        VALUES (:question, :status , :user_id)
        RETURNING id, user_id, question, status, created_at
    """)
    try:   
        with get_db_connection() as connection:
            result= connection.execute(
            INSERT_QUERY,
            {"question": request.query, "status": "pending" ,"user_id": current_user["id"]}
        )

            research=result.mappings().one()
            return  dict(research)
    except Exception as e:
        print(f"Error occurred: {e}")
        return {"message": "An error occurred while processing the research request"}


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
        SELECT id, question, status, user_id, created_at
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

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch research records"
        )



@router.get("/researches/{research_id}")
def get_research(research_id:int , current_user: dict = Depends(get_current_user)):
    SELECT_QUERY=text("""
    SELECT * from researches 
    WHERE id=:research_id
        AND user_id = :user_id
    """)    
    try:
        with get_db_connection() as connection:
            result=connection.execute(SELECT_QUERY , {"research_id":research_id , "user_id": current_user["id"]})
            research=result.mappings().one_or_none()
            if research:
                return dict(research)
            else:
                return {"message " : f"Research with id {research_id} not found "}
    except Exception as e:
        print(f"Error occured: {e}")
        return {"message ": "An error occurred while fetching the research record"}        

class ResearchStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"            

class ResearchUpdateRequest(BaseModel):
    status: ResearchStatus = Field(
        description="Updated research status"
    )
@router.patch("/researches/{research_id}")
async def update_research(research_id:int, request:ResearchUpdateRequest , current_user: dict = Depends(get_current_user)):
    
    UPDATE_QUERY=text("""
    UPDATE researches
    SET status=:status
    WHERE id=:research_id
    AND user_id = :user_id
    """)
    try:
        with get_db_connection() as connection:
            result=connection.execute(UPDATE_QUERY, {"status":request.status.value , "research_id":research_id , "user_id": current_user["id"],})
            if result.rowcount==0:
                return {"message":f"Research with id {research_id} not found"}
            return {"message":f"Research with id {research_id} updated successfully"}
    except Exception as e:
        print(f"Error occured: {e}")
        return {"message": "An error occurred while updating the research record"}

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
    
    