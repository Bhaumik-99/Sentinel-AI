import time
from pathlib import Path
import cv2
from .config import settings
from .database import add_events, create_video, finish_video
from .detector import get_model

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

def process_video(path: Path, original_filename: str) -> dict:
    if path.suffix.lower() not in VIDEO_EXTENSIONS:
        raise ValueError("Unsupported video format. Use MP4, MOV, AVI, MKV, or WEBM.")
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError("The uploaded file could not be opened as a video.")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = frame_count / fps if fps > 0 else 0.0
    video_id = create_video(original_filename, str(path), duration, fps, frame_count)
    interval = max(0.1, settings.sample_interval)
    frame_step = max(1, round((fps if fps > 0 else 25) * interval))
    model = get_model()
    start = time.perf_counter()
    frame_no = processed = 0
    batch = []
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if frame_no % frame_step == 0:
                result = model.track(frame, persist=True, tracker="bytetrack.yaml", verbose=False)[0]
                boxes = result.boxes
                if boxes is not None:
                    xyxy = boxes.xyxy.cpu().tolist()
                    confs = boxes.conf.cpu().tolist()
                    classes = boxes.cls.cpu().tolist()
                    ids = boxes.id.int().cpu().tolist() if boxes.id is not None else [None] * len(xyxy)
                    for box, conf, cls, track_id in zip(xyxy, confs, classes, ids):
                        x1, y1, x2, y2 = box
                        batch.append({
                            "video_id": video_id,
                            "timestamp_seconds": round(frame_no / fps, 3) if fps > 0 else 0.0,
                            "frame_number": frame_no,
                            "label": str(result.names[int(cls)]),
                            "confidence": float(conf),
                            "track_id": int(track_id) if track_id is not None else None,
                            "x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2),
                        })
                processed += 1
                if len(batch) >= 500:
                    add_events(video_id, batch)
                    batch.clear()
            frame_no += 1
        if batch:
            add_events(video_id, batch)
        elapsed = time.perf_counter() - start
        finish_video(video_id, processed, elapsed)
        return {
            "video_id": video_id, "filename": original_filename,
            "duration_seconds": round(duration, 2), "fps": round(fps, 2),
            "frame_count": frame_count, "processed_frames": processed,
            "processing_seconds": round(elapsed, 3), "sample_interval_seconds": interval,
        }
    finally:
        cap.release()
