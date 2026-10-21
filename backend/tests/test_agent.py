from app import agent

def test_unknown_agent_tool_is_rejected():
    assert agent.run_tool("run_shell", {}) == {"error": "Unknown tool"}

def test_search_tool_returns_timestamped_events(monkeypatch):
    monkeypatch.setattr(agent, "search_events", lambda **kwargs: [
        {"id": 8, "video_id": 2, "timestamp_seconds": 4.25, "label": "person", "confidence": 0.9, "track_id": 3}
    ])
    result = agent.run_tool("search_events", {"label": "person", "limit": 10}, scope=2)
    assert result["events"][0]["timestamp_seconds"] == 4.25
    assert result["events"][0]["label"] == "person"

def test_video_summary_handles_missing_video(monkeypatch):
    monkeypatch.setattr(agent, "get_video", lambda video_id: None)
    assert agent.run_tool("video_summary", {"video_id": 999}) == {"error": "Video not found"}
