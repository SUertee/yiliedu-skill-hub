from fastapi import FastAPI
from app.skills.lesson_sync import router as lesson_sync_router
from app.skills.stt_volc.stt_volc import router as stt_volc_router
from app.skills.teacher_search.router import router as teacher_search_router

app = FastAPI(title="Skill Hub", version="0.1.0")

app.include_router(teacher_search_router)
app.include_router(stt_volc_router)
app.include_router(lesson_sync_router)

@app.get("/healthz")
def healthz():
    return {"ok": True}
