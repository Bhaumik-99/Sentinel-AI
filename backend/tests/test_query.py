from app import query

def test_empty_question():
    result = query.answer_question("   ")
    assert result["evidence"] == []
    assert "enter a question" in result["answer"].lower()

def test_object_question_returns_timestamped_evidence(monkeypatch):
    monkeypatch.setattr(query, "search_events", lambda **kwargs: [
        {"id": 1, "video_id": 7, "timestamp_seconds": 1.5, "frame_number": 45, "label": "person", "confidence": 0.91, "track_id": 2},
        {"id": 2, "video_id": 7, "timestamp_seconds": 3.0, "frame_number": 90, "label": "person", "confidence": 0.88, "track_id": 2},
        {"id": 3, "video_id": 7, "timestamp_seconds": 4.0, "frame_number": 120, "label": "car", "confidence": 0.79, "track_id": 4},
    ])
    result = query.answer_question("When was a person detected?", video_id=7)
    assert "Found 2 stored detections" in result["answer"]
    assert result["evidence"][0]["timestamp_seconds"] == 1.5
    assert result["total_matching_events"] == 2

def test_empty_database_result_is_cautious(monkeypatch):
    monkeypatch.setattr(query, "search_events", lambda **kwargs: [])
    result = query.answer_question("Was a person present?")
    assert result["evidence"] == []
    assert "does not prove" in result["answer"]
