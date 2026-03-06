from fastapi import FastAPI
from app.skills.lesson_sync import router as lesson_sync_router
from app.skills.mlh_st_psy_search.router import router as mlh_st_psy_search_router
from app.skills.volc_tts.router import router as volc_tts_router
from app.skills.teacher_search.router import router as teacher_search_router

try:
    from app.skills.stt_volc.stt_volc import router as stt_volc_router
except ModuleNotFoundError:
    from app.skills.volc_stt.stt_volc import router as stt_volc_router

app = FastAPI(title="Skill Hub", version="0.1.0")

app.include_router(teacher_search_router)
app.include_router(mlh_st_psy_search_router)
app.include_router(stt_volc_router)
app.include_router(volc_tts_router)
app.include_router(lesson_sync_router)

@app.get("/healthz")
def healthz():
    return {"ok": True}
