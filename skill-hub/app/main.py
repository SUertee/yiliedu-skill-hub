from app.skills.lesson_sync import router as lesson_sync_router
from app.skills.mlh_st_psy_search.router import router as mlh_st_psy_search_router
from app.skills.teacher_search.router import router as teacher_search_router
from app.skills.volc_stt.router import router as volc_stt_router
from app.skills.volc_tts.router import router as volc_tts_router
from fastapi import FastAPI

app = FastAPI(title="Skill Hub", version="0.1.0")

app.include_router(teacher_search_router)
app.include_router(mlh_st_psy_search_router)
app.include_router(volc_stt_router)
app.include_router(volc_tts_router)
app.include_router(lesson_sync_router)


@app.get("/healthz")
def healthz():
    return {"ok": True}
