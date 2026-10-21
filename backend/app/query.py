from collections import Counter
from .database import search_events

def answer_question(question: str, video_id: int | None = None) -> dict:
    q = question.strip().lower()
    if not q:
        return {"answer": "Please enter a question.", "evidence": [], "method": "validation"}

    # Search a class when the question names one; otherwise summarize retrieved events.
    events = search_events(video_id=video_id, limit=500)
    if not events:
        scope = f" in video {video_id}" if video_id else ""
        return {
            "answer": f"No stored detections were found{scope}. This does not prove an object was absent; the detector may have missed it.",
            "evidence": [],
            "method": "SQLite event retrieval; no generative model used",
        }

    labels = sorted({str(e["label"]).lower() for e in events}, key=len, reverse=True)
    label = next((item for item in labels if item in q), None)
    if label:
        matching = [e for e in events if str(e["label"]).lower() == label]
        if not matching:
            matching = []
        if matching:
            events = matching
            answer = (
                f"Found {len(matching)} stored detections of '{label}'. "
                f"The first is at {matching[0]['timestamp_seconds']:.2f}s and the last is at "
                f"{matching[-1]['timestamp_seconds']:.2f}s."
            )
        else:
            answer = f"No stored detections of '{label}' were found in the retrieved events."
    else:
        counts = Counter(str(e["label"]) for e in events)
        summary = ", ".join(f"{name}: {count}" for name, count in counts.most_common(8))
        first, last = events[0], events[-1]
        answer = (
            f"Retrieved {len(events)} stored detections between {first['timestamp_seconds']:.2f}s "
            f"and {last['timestamp_seconds']:.2f}s. Most frequent labels: {summary}."
        )

    evidence = [{
        "event_id": e["id"], "video_id": e["video_id"],
        "timestamp_seconds": e["timestamp_seconds"], "frame_number": e["frame_number"],
        "label": e["label"], "confidence": round(e["confidence"], 4), "track_id": e["track_id"],
    } for e in events[:20]]
    return {
        "answer": answer,
        "evidence": evidence,
        "method": "Evidence-grounded retrieval; answers only from stored detections",
        "total_matching_events": len(events),
    }
