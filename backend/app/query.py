from .database import search_events

def answer_question(question: str, video_id: int | None = None) -> dict:
    q = question.strip().lower()
    if not q:
        return {"answer": "Please enter a question.", "evidence": []}
    known_labels = ["person", "car", "truck", "bus", "bicycle", "motorcycle", "dog", "cat", "chair", "bottle"]
    label = next((name for name in known_labels if name in q), None)
    events = search_events(video_id=video_id, label=label, limit=200)
    if not events:
        scope = f" in video {video_id}" if video_id else ""
        return {
            "answer": f"I could not find matching stored detections{scope}. This does not prove the object never occurred; the detector may have missed it.",
            "evidence": [],
            "method": "SQLite event retrieval; no generative model used",
        }
    first, last = events[0], events[-1]
    if label:
        answer = f"Found {len(events)} stored detections of '{label}'. The first is at {first['timestamp_seconds']:.2f}s and the last is at {last['timestamp_seconds']:.2f}s."
    else:
        counts = {}
        for event in events:
            counts[event["label"]] = counts.get(event["label"], 0) + 1
        summary = ", ".join(f"{k}: {v}" for k, v in sorted(counts.items(), key=lambda x: -x[1])[:8])
        answer = f"Retrieved {len(events)} stored detections. Most frequent labels in the returned evidence: {summary}."
    return {
        "answer": answer,
        "evidence": [{
            "event_id": e["id"], "video_id": e["video_id"],
            "timestamp_seconds": e["timestamp_seconds"], "frame_number": e["frame_number"],
            "label": e["label"], "confidence": round(e["confidence"], 4), "track_id": e["track_id"],
        } for e in events[:20]],
        "method": "Evidence-grounded retrieval; answers only from stored detections",
    }
