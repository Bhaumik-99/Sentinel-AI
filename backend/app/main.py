from pathlib import Path
import uuid
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .config import settings
from .database import init_db, list_videos, search_events, get_video
from .pipeline import process_video
from .query import answer_question

app = FastAPI(title="Sentinel AI", version="0.1.0", description="Video intelligence MVP with evidence-grounded event search.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

@app.on_event("startup")
def startup() -> None:
    settings.upload_path
    init_db()

@app.get("/health")
def health():
    return {"status": "ok", "service": "sentinel-ai"}

@app.get("/api/videos")
def videos():
    return {"items": list_videos()}

@app.post("/api/videos")
async def upload_video(file: UploadFile = File(...)):
    filename = Path(file.filename or "upload.mp4").name
    suffix = Path(filename).suffix.lower()
    if suffix not in {".mp4", ".mov", ".avi", ".mkv", ".webm"}:
        raise HTTPException(400, "Unsupported format. Upload MP4, MOV, AVI, MKV, or WEBM.")
    destination = settings.upload_path / filename
    if destination.exists():
        destination = settings.upload_path / f"{destination.stem}_{uuid.uuid4().hex[:8]}{suffix}"
    max_bytes, size = settings.max_video_mb * 1024 * 1024, 0
    try:
        with destination.open("wb") as out:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    destination.unlink(missing_ok=True)
                    raise HTTPException(413, f"File exceeds the {settings.max_video_mb} MB limit.")
                out.write(chunk)
        result = process_video(destination, filename)
        return {"status": "processed", **result}
    except HTTPException:
        raise
    except ValueError as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, f"Processing failed: {type(exc).__name__}: {exc}") from exc
    finally:
        await file.close()

@app.get("/api/events")
def events(video_id: int | None = None, label: str | None = None, limit: int = Query(100, ge=1, le=500)):
    if video_id is not None and get_video(video_id) is None:
        raise HTTPException(404, "Video not found.")
    return {"items": search_events(video_id=video_id, label=label, limit=limit)}

class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    video_id: int | None = None

@app.post("/api/ask")
def ask(body: AskRequest):
    if body.video_id is not None and get_video(body.video_id) is None:
        raise HTTPException(404, "Video not found.")
    return answer_question(body.question, body.video_id)
