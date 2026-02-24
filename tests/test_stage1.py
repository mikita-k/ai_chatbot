import os
import tempfile
import shutil
import numpy as np
from src.stage1.rag_chatbot import DocumentStore, guard_rails, SimpleRAGChatbot


def test_guard_rails_email_redaction():
    txt = "Contact me at foo.bar@example.com"
    red = guard_rails(txt)
    assert "[REDACTED_EMAIL]" in red


def test_guard_rails_number_redaction():
    txt = "My passport is 123456789 and credit card 9876543210"
    red = guard_rails(txt)
    assert "[REDACTED_NUMBER]" in red


def test_documentstore_retrieval():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "static_docs.txt")
    path = os.path.abspath(path)

    # Use temporary directory for FAISS DB to avoid conflicts
    with tempfile.TemporaryDirectory() as tmpdir:
        store = DocumentStore.from_file(path, db_path=tmpdir)
        hits = store.retrieve("pricing", k=2)
        assert len(hits) == 2
        # Both hits should have similarity scores (float or numpy float)
        assert all(isinstance(score, (float, np.floating)) and 0.0 <= score <= 1.0 for _, score in hits)


def test_simple_rag_answer():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "static_docs.txt")
    path = os.path.abspath(path)

    # Use temporary directory for FAISS DB
    with tempfile.TemporaryDirectory() as tmpdir:
        store = DocumentStore.from_file(path, db_path=tmpdir)
        bot = SimpleRAGChatbot(store)
        ans = bot.answer("where is the parking", k=3)
        # Check that answer contains retrieved content
        assert len(ans) > 0
        assert "similarity" in ans.lower() or "location" in ans.lower() or "parking" in ans.lower()


def test_dynamic_data_included():
    """Test that dynamic parking data is included in the answer."""
    path = os.path.join(os.path.dirname(__file__), "..", "data", "static_docs.txt")
    path = os.path.abspath(path)

    with tempfile.TemporaryDirectory() as tmpdir:
        store = DocumentStore.from_file(path, db_path=tmpdir)
        bot = SimpleRAGChatbot(store, include_dynamic=True)
        ans = bot.answer("how many parking spaces", k=3)

        # Check that answer includes dynamic data markers
        assert "REAL-TIME PARKING INFORMATION" in ans or "Current Availability" in ans or "available" in ans.lower()


