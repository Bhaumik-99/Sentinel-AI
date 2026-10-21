import sqlite3
from pathlib import Path
from typing import Any
from .config import settings

def connect() -> sqlite3.Connection:
    db_path = Path(settings.db_path)
    if not db_path.is_absolute():
        db_path = Path(__file__).resolve().parents[1] / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db() -> None:
    with connect() as conn:
        conn.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            stored_path TEXT NOT NULL,
            duration_seconds REAL NOT NULL DEFAULT 0,
            fps REAL NOT NULL DEFAULT 0,
            frame_count INTEGER NOT NULL DEFAULT 0,
            processed_frames INTEGER NOT NULL DEFAULT 0,
            processing_seconds REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
            timestamp_seconds REAL NOT NULL,
            frame_number INTEGER NOT NULL,
            label TEXT NOT NULL,
            confidence REAL NOT NULL,
            track_id INTEGER,
            x1 REAL NOT NULL, y1 REAL NOT NULL, x2 REAL NOT NULL, y2 REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_events_video_time ON events(video_id, timestamp_seconds);
        CREATE INDEX IF NOT EXISTS idx_events_label ON events(label);
        """)

def create_video(filename: str, stored_path: str, duration: float, fps: float, frame_count: int) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO videos(filename,stored_path,duration_seconds,fps,frame_count) VALUES(?,?,?,?,?)",
            (filename, stored_path, duration, fps, frame_count),
        )
        return int(cur.lastrowid)

def add_events(video_id: int, events: list[dict[str, Any]]) -> None:
    if not events:
        return
    with connect() as conn:
        conn.executemany("""
        INSERT INTO events(video_id,timestamp_seconds,frame_number,label,confidence,track_id,x1,y1,x2,y2)
        VALUES(:video_id,:timestamp_seconds,:frame_number,:label,:confidence,:track_id,:x1,:y1,:x2,:y2)
        """, events)

def finish_video(video_id: int, processed_frames: int, processing_seconds: float) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE videos SET processed_frames=?, processing_seconds=? WHERE id=?",
            (processed_frames, processing_seconds, video_id),
        )

def list_videos() -> list[dict[str, Any]]:
    with connect() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT id,filename,duration_seconds,fps,frame_count,processed_frames,processing_seconds,created_at FROM videos ORDER BY id DESC"
        )]

def get_video(video_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM videos WHERE id=?", (video_id,)).fetchone()
        return dict(row) if row else None

def delete_video(video_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM videos WHERE id=?", (video_id,)).fetchone()
        if row is None:
            return None
        result = dict(row)
        conn.execute("DELETE FROM events WHERE video_id=?", (video_id,))
        conn.execute("DELETE FROM videos WHERE id=?", (video_id,))
        return result

def search_events(video_id: int | None = None, label: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    clauses, params = [], []
    if video_id is not None:
        clauses.append("video_id=?"); params.append(video_id)
    if label:
        clauses.append("LOWER(label)=LOWER(?)"); params.append(label.strip())
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(max(1, min(limit, 500)))
    with connect() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM events" + where + " ORDER BY timestamp_seconds ASC LIMIT ?", params
        )]
