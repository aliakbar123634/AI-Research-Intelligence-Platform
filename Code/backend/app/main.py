from fastapi import FastAPI
from .health import router as health_router
from .research import router as research_router
from .auth import router as auth_router

app=FastAPI(
    title="AI Research & Intelligence Platform",
    description="AI-powered research and intelligence API",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {
        "message": "AI Research & Intelligence Platform API"
    }

app.include_router(health_router)
app.include_router(research_router)
app.include_router(auth_router)


#    cd Code
#    cd backend
#    .\venv\Scripts\Activate.ps1         
#    python -m uvicorn app.main:app --reload
#    http://127.0.0.1:8000/docs