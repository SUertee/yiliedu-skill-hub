from fastapi import FastAPI
from app.skills.teacher_search.router import router as teacher_search_router

app = FastAPI(title="Skill Hub", version="0.1.0")

app.include_router(teacher_search_router)

@app.get("/healthz")
def healthz():
    return {"ok": True}
