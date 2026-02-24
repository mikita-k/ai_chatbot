"""
Tests for Stage 2 LangChain: Human-in-the-Loop Admin Agent

Tests cover:
- LangChain tools creation and execution
- Admin agent request submission
- Admin approval/rejection workflow
- Database persistence
- Telegram channel integration
- Full chatbot workflow with approvals
"""

import os
import tempfile
import time
import pytest
from src.stage2.admin_agent import (
    AdminAgent,
    create_admin_agent,
)
from src.stage2.database import (
    ReservationRequest,
    AdminApprovalDatabase,
)
from src.stage2.approval_channels import (
    SimulatedApprovalChannel,
    TelegramApprovalChannel,
)


class TestReservationRequest:
    """Test ReservationRequest data class."""

    def test_creation(self):
        """Test creating a reservation request."""
        req = ReservationRequest(
            request_id="REQ-20260220120000-001",
            name="John",
            surname="Doe",
            car_number="ABC123",
            period="2026-02-20 10:00 - 12:00",
            created_at="2026-02-20T12:00:00"
        )

        assert req.request_id == "REQ-20260220120000-001"
        assert req.name == "John"
        assert req.status == "pending"
        assert req.to_dict()["name"] == "John"

    def test_string_representation(self):
        """Test string representation of request."""
        req = ReservationRequest(
            request_id="REQ-001",
            name="Jane",
            surname="Smith",
            car_number="XYZ789",
            period="2026-02-20 14:00 - 16:00",
            created_at="2026-02-20T14:00:00"
        )

        str_repr = str(req)
        assert "Jane Smith" in str_repr
        assert "XYZ789" in str_repr
        assert "pending" in str_repr


class TestAdminApprovalDatabase:
    """Test SQLite database for approvals."""

    def test_database_creation(self):
        """Test that database is created correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = AdminApprovalDatabase(db_path)

            assert os.path.exists(db_path)

    def test_save_and_retrieve_request(self):
        """Test saving and retrieving requests from database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = AdminApprovalDatabase(db_path)

            # Create and save a request
            req = ReservationRequest(
                request_id="REQ-001",
                name="Alice",
                surname="Wonder",
                car_number="DEF456",
                period="2026-02-21 09:00 - 11:00",
                created_at="2026-02-20T15:00:00"
            )
            db.save_request(req)

            # Retrieve it
            retrieved = db.get_request("REQ-001")
            assert retrieved is not None
            assert retrieved.name == "Alice"
            assert retrieved.surname == "Wonder"

    def test_get_all_requests_filtered(self):
        """Test retrieving requests with status filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = AdminApprovalDatabase(db_path)

            # Save multiple requests with different statuses
            req1 = ReservationRequest(
                request_id="REQ-001",
                name="User1",
                surname="Test",
                car_number="ABC111",
                period="2026-02-20 10:00 - 12:00",
                created_at="2026-02-20T10:00:00",
                status="pending"
            )
            req2 = ReservationRequest(
                request_id="REQ-002",
                name="User2",
                surname="Test",
                car_number="ABC222",
                period="2026-02-20 14:00 - 16:00",
                created_at="2026-02-20T14:00:00",
                status="approved"
            )

            db.save_request(req1)
            db.save_request(req2)

            # Filter by pending
            pending = db.get_all_requests(status="pending")
            assert len(pending) == 1
            assert pending[0].request_id == "REQ-001"

            # Filter by approved
            approved = db.get_all_requests(status="approved")
            assert len(approved) == 1
            assert approved[0].request_id == "REQ-002"

            # All requests
            all_reqs = db.get_all_requests()
            assert len(all_reqs) == 2


class TestSimulatedApprovalChannel:
    """Test the simulated approval channel (for testing)."""

    def test_send_request(self):
        """Test sending a request through simulated channel."""
        channel = SimulatedApprovalChannel(auto_approve=False)

        req = ReservationRequest(
            request_id="REQ-001",
            name="Bob",
            surname="Builder",
            car_number="BLD123",
            period="2026-02-20 08:00 - 10:00",
            created_at="2026-02-20T08:00:00"
        )

        assert channel.send_request(req)
        assert req.request_id in channel.pending_requests

    def test_auto_approval(self):
        """Test automatic approval after delay."""
        channel = SimulatedApprovalChannel(auto_approve=True, approval_delay_sec=0.1)

        req = ReservationRequest(
            request_id="REQ-AUTO",
            name="Auto",
            surname="Bot",
            car_number="AUTO01",
            period="2026-02-20 11:00 - 13:00",
            created_at="2026-02-20T11:00:00"
        )

        channel.send_request(req)

        # Wait for auto-approval
        time.sleep(0.3)

        # Get responses
        responses = channel.get_responses()
        assert len(responses) == 1
        assert responses[0]["request_id"] == "REQ-AUTO"
        assert responses[0]["approved"]


class TestLangChainAdminAgent:
    """Test the LangChain AdminAgent class."""

    def test_tools_created(self):
        """Test that LangChain tools are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            agent = AdminAgent(
                approval_channel=SimulatedApprovalChannel(auto_approve=False),
                db_path=db_path
            )

            # Check that tools were created
            assert len(agent.tools) > 0
            tool_names = [tool.name for tool in agent.tools]
            assert "submit_reservation" in tool_names
            assert "check_request_status" in tool_names
            assert "process_admin_responses" in tool_names

    def test_submit_request(self):
        """Test submitting a reservation request."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            agent = AdminAgent(
                approval_channel=SimulatedApprovalChannel(auto_approve=False),
                db_path=db_path
            )

            req_id = agent.submit_request(
                name="Charlie",
                surname="Brown",
                car_number="CRB789",
                period="2026-02-20 16:00 - 18:00"
            )

            assert req_id.startswith("REQ-")

            # Verify it's in the database
            status = agent.check_status(req_id)
            assert status["status"] == "pending"
            assert status["approved"] is False

    def test_approval_workflow(self):
        """Test the complete approval workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            agent = AdminAgent(
                approval_channel=SimulatedApprovalChannel(auto_approve=True, approval_delay_sec=0.1),
                db_path=db_path
            )

            # Submit request
            req_id = agent.submit_request(
                name="Diana",
                surname="Prince",
                car_number="WW1984",
                period="2026-02-21 09:00 - 11:00"
            )

            # Wait for auto-approval
            time.sleep(0.2)

            # Process responses
            agent.process_responses()

            # Check final status
            status = agent.check_status(req_id)
            assert status["status"] == "approved"
            assert status["approved"] is True

    def test_rejection_workflow(self):
        """Test request rejection workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            channel = SimulatedApprovalChannel(auto_approve=False)
            agent = AdminAgent(approval_channel=channel, db_path=db_path)

            # Submit request
            req_id = agent.submit_request(
                name="Eve",
                surname="Anderson",
                car_number="EVE123",
                period="2026-02-21 13:00 - 15:00"
            )

            # Simulate admin rejection
            channel.add_response(
                request_id=req_id,
                approved=False,
                reason="No available parking for this time slot"
            )

            # Process responses
            agent.process_responses()

            # Check status
            status = agent.check_status(req_id)
            assert status["status"] == "rejected"
            assert status["approved"] is False
            assert "No available parking" in status["reason"]

    def test_pending_requests_list(self):
        """Test retrieving list of pending requests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            agent = AdminAgent(
                approval_channel=SimulatedApprovalChannel(auto_approve=False),
                db_path=db_path
            )

            # Submit multiple requests
            req1 = agent.submit_request("Frank", "Sinatra", "FS1015", "2026-02-20 10:00 - 12:00")
            req2 = agent.submit_request("Grace", "Hopper", "GH1906", "2026-02-20 14:00 - 16:00")

            # Get pending
            pending = agent.get_pending_requests()
            assert len(pending) == 2

            # Approve one
            agent.approval_channel.add_response(req1, True)
            agent.process_responses()

            # Now only one pending
            pending = agent.get_pending_requests()
            assert len(pending) == 1
            assert pending[0]["request_id"] == req2

    def test_get_all_requests(self):
        """Test getting all requests (for reporting)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            agent = AdminAgent(
                approval_channel=SimulatedApprovalChannel(auto_approve=False),
                db_path=db_path
            )

            # Submit requests
            req1 = agent.submit_request("Henry", "Ford", "HF1863", "2026-02-20 08:00 - 10:00")
            req2 = agent.submit_request("Iris", "West", "IW2000", "2026-02-21 10:00 - 12:00")

            all_reqs = agent.get_all_requests()
            assert len(all_reqs) == 2
            assert any(r["request_id"] == req1 for r in all_reqs)
            assert any(r["request_id"] == req2 for r in all_reqs)


class TestCreateAdminAgent:
    """Test the factory function for creating admin agents."""

    def test_create_with_simulated_channel(self):
        """Test creating agent with simulated channel."""
        agent = create_admin_agent(use_telegram=False)

        assert agent is not None
        assert isinstance(agent.approval_channel, SimulatedApprovalChannel)

    def test_create_with_telegram_missing_vars(self):
        """Test that Telegram channel requires env vars."""
        # Make sure env vars are not set
        os.environ.pop("TELEGRAM_BOT_TOKEN", None)
        os.environ.pop("TELEGRAM_ADMIN_CHAT_ID", None)

        with pytest.raises(ValueError):
            create_admin_agent(use_telegram=True)


class TestStage2Integration:
    """Integration tests for Stage 2 LangChain chatbot."""

    def test_full_workflow_with_chatbot(self):
        """Test the complete Stage 2 workflow with the integrated chatbot."""
        from src.stage2.chatbot_with_approval import Stage2Chatbot
        from src.stage1.rag_chatbot import DocumentStore

        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize Stage 1
            rag_path = os.path.join(os.path.dirname(__file__), "..", "data", "static_docs.txt")
            rag_path = os.path.abspath(rag_path)
            store = DocumentStore.from_file(rag_path, db_path=os.path.join(tmpdir, "faiss"))

            # Initialize Stage 2 LangChain
            db_path = os.path.join(tmpdir, "approvals.db")
            admin_agent = AdminAgent(
                approval_channel=SimulatedApprovalChannel(auto_approve=True, approval_delay_sec=0.1),
                db_path=db_path
            )

            # Create integrated chatbot
            chatbot = Stage2Chatbot(store, admin_agent, use_llm=False)

            # Test: Ask a question
            answer = chatbot.answer_question("where is the parking")
            assert len(answer) > 0
            assert "location" in answer.lower() or "parking" in answer.lower()

            # Test: Initiate reservation
            result = chatbot.initiate_reservation({
                "name": "Jack",
                "surname": "Sparrow",
                "car_number": "PEARL01",
                "period": "2026-02-20 10:00 - 12:00"
            })

            assert result["success"]
            req_id = result["request_id"]
            assert req_id.startswith("REQ-")

            # Check initial status
            status = chatbot.check_request_status(req_id)
            assert status["status"] == "pending"

            # Wait for auto-approval
            time.sleep(0.2)
            admin_agent.process_responses()

            # Check final status
            status = chatbot.check_request_status(req_id)
            assert status["status"] == "approved"
            assert status["approved"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

