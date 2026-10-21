from app.query import answer_question

def test_empty_question():
    result = answer_question("   ")
    assert result["evidence"] == []
    assert "enter a question" in result["answer"].lower()
