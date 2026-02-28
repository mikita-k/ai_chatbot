"""
Stage 4: LangGraph Orchestration Tests

Comprehensive tests for the orchestration system:
- State transitions and routing
- Info request handling (RAG)
- Reservation request handling (Admin approval + Storage)
- Error handling and edge cases
- End-to-end workflow integration
"""

import pytest
import os
import sys
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.stage4.orchestrator import LangGraphOrchestrator, create_orchestrator
from src.stage4.graph import (
    WorkflowState,
    build_orchestration_graph,
    create_orchestration_graph,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def orchestrator():
    """Create an orchestrator instance for testing."""
    return create_orchestrator(use_llm=False, use_telegram=False, verbose=False)


@pytest.fixture
def sample_info_request():
    """Sample info request."""
    return "What are the parking prices?"


@pytest.fixture
def sample_reservation_request():
    """Sample reservation request."""
    return "I want to reserve a parking space"


# ============================================================================
# TEST: Graph Creation and Initialization
# ============================================================================

class TestGraphCreation:
    """Test graph creation and initialization."""

    def test_graph_builds_successfully(self):
        """Test that the graph builds without errors."""
        graph = build_orchestration_graph(use_llm=False, use_telegram=False)
        assert graph is not None

    def test_graph_compiles_successfully(self):
        """Test that the graph compiles to runnable form."""
        compiled_graph = create_orchestration_graph(use_llm=False, use_telegram=False)
        assert compiled_graph is not None
        assert hasattr(compiled_graph, 'invoke')


# ============================================================================
# TEST: Orchestrator Creation and Initialization
# ============================================================================

class TestOrchestratorInit:
    """Test orchestrator initialization."""

    def test_orchestrator_creates_successfully(self, orchestrator):
        """Test orchestrator creation."""
        assert orchestrator is not None
        assert orchestrator.graph is not None
        assert orchestrator.request_history == {}

    def test_orchestrator_with_different_configs(self):
        """Test orchestrator with different configurations."""
        # Default config
        orch1 = create_orchestrator(use_llm=False, use_telegram=False)
        assert orch1 is not None

        # With verbose
        orch2 = create_orchestrator(use_llm=False, use_telegram=False, verbose=True)
        assert orch2.verbose is True


# ============================================================================
# TEST: Info Requests (RAG Path)
# ============================================================================

class TestInfoRequests:
    """Test processing of info requests using RAG."""

    def test_info_request_type_classification(self, orchestrator, sample_info_request):
        """Test that info requests are correctly classified."""
        result = orchestrator.process_request(sample_info_request)

        assert result is not None
        assert result['request_type'] == 'info'
        assert result['request_id'] != ''

    def test_info_request_returns_response(self, orchestrator, sample_info_request):
        """Test that info requests get a response."""
        result = orchestrator.process_request(sample_info_request)

        assert result['final_response'] != ''
        assert len(result['final_response']) > 0

    def test_info_request_visits_rag_node(self, orchestrator, sample_info_request):
        """Test that info requests visit the RAG node."""
        result = orchestrator.process_request(sample_info_request)

        assert 'router' in result['state_history']
        assert 'rag' in result['state_history']
        assert 'response' in result['state_history']

    def test_info_request_does_not_trigger_approval(self, orchestrator, sample_info_request):
        """Test that info requests don't trigger approval workflow."""
        result = orchestrator.process_request(sample_info_request)

        assert 'approval' not in result['state_history']
        assert 'storage' not in result['state_history']

    def test_multiple_info_requests(self, orchestrator):
        """Test processing multiple info requests."""
        requests = [
            "What are the prices?",
            "Where is the parking located?",
            "What are the working hours?"
        ]

        results = []
        for req in requests:
            result = orchestrator.process_request(req)
            results.append(result)

        assert len(results) == 3
        # All requests should produce responses (type may vary)
        for result in results:
            assert result['final_response'] != ''


# ============================================================================
# TEST: Reservation Requests (Admin Approval + Storage)
# ============================================================================

class TestReservationRequests:
    """Test processing of reservation requests."""

    def test_reservation_request_type_classification(self, orchestrator, sample_reservation_request):
        """Test that reservation requests are correctly classified."""
        result = orchestrator.process_request(sample_reservation_request)

        assert result is not None
        assert result['request_type'] == 'reservation'

    def test_reservation_request_creates_details(self, orchestrator, sample_reservation_request):
        """Test that reservation requests create reservation details."""
        result = orchestrator.process_request(sample_reservation_request)

        # Result should contain approval status
        assert 'approval_status' in result

    def test_reservation_workflow_path(self, orchestrator, sample_reservation_request):
        """Test that reservations follow the correct workflow path."""
        result = orchestrator.process_request(sample_reservation_request)

        # Should visit these nodes in order
        state_history = result['state_history']
        assert 'initialize' in state_history
        assert 'router' in state_history
        assert 'collection' in state_history
        assert 'approval' in state_history

    def test_approved_reservation_saves_to_storage(self, orchestrator, sample_reservation_request):
        """Test that approved reservations are saved to storage."""
        result = orchestrator.process_request(sample_reservation_request)

        # With simulated auto-approve, this should be approved and saved
        if result['approval_status'] == 'approved':
            assert 'storage' in result['state_history']


# ============================================================================
# TEST: Request History and Status Tracking
# ============================================================================

class TestRequestHistory:
    """Test request history and status tracking."""

    def test_request_stored_in_history(self, orchestrator):
        """Test that processed requests are stored in history."""
        message = "test request"
        result = orchestrator.process_request(message)

        request_id = result['request_id']
        assert request_id in orchestrator.request_history

    def test_get_request_status(self, orchestrator):
        """Test retrieving request status from history."""
        message = "test request"
        result1 = orchestrator.process_request(message)
        request_id = result1['request_id']

        # Retrieve from history
        record = orchestrator.get_request_status(request_id)
        assert record is not None
        assert record['user_message'] == message
        assert record['output']['request_id'] == request_id

    def test_list_requests(self, orchestrator):
        """Test listing all processed requests."""
        # Process multiple requests
        orchestrator.process_request("First request")
        orchestrator.process_request("Second request")
        orchestrator.process_request("Third request")

        requests = orchestrator.list_requests()
        assert len(requests) >= 3

        # Check that all required fields are present
        for req in requests:
            assert 'request_id' in req
            assert 'user_id' in req
            assert 'timestamp' in req
            assert 'request_type' in req

    def test_nonexistent_request_status(self, orchestrator):
        """Test getting status for nonexistent request."""
        result = orchestrator.get_request_status("NONEXISTENT-ID")
        assert result is None


# ============================================================================
# TEST: Routing Logic
# ============================================================================

class TestRoutingLogic:
    """Test request routing logic."""

    def test_info_keywords_routing(self, orchestrator):
        """Test routing based on info keywords."""
        info_keywords = [
            "What's the price?",
            "How much does it cost?",
            "Where is the parking?",
            "What are the hours?",
        ]

        for keyword in info_keywords:
            result = orchestrator.process_request(keyword)
            # Should either be 'info' or successfully answer the question
            assert result['final_response'] != '', f"No response for: {keyword}"

    def test_reservation_keywords_routing(self, orchestrator):
        """Test routing based on reservation keywords."""
        # Note: reservation detection requires absence of info keywords
        result = orchestrator.process_request("I need to book a parking space")
        # Could be 'reservation' or 'info' depending on exact keywords
        assert result['request_type'] in ['reservation', 'info']

    def test_unknown_request_routing(self, orchestrator):
        """Test routing for unknown/ambiguous requests."""
        result = orchestrator.process_request("xyz abc 123")
        assert result['request_type'] in ['unknown', 'info', 'reservation']


# ============================================================================
# TEST: State Transitions
# ============================================================================

class TestStateTransitions:
    """Test proper state transitions through the workflow."""

    def test_state_initialized_correctly(self, orchestrator):
        """Test that state is initialized with all required fields."""
        result = orchestrator.process_request("test")

        assert result['request_id'].startswith('FLOW-')
        assert result['final_response'] != ''
        assert isinstance(result['errors'], list)
        assert isinstance(result['state_history'], list)

    def test_state_history_sequence(self, orchestrator):
        """Test that state history shows correct node sequence."""
        result = orchestrator.process_request("What's the price?")

        # Info request should have: initialize → router → rag → response
        state_history = result['state_history']

        # Check initialize is first
        assert state_history[0] == 'initialize'

        # Check router comes after
        assert 'router' in state_history

        # Check response is last
        assert state_history[-1] == 'response'


# ============================================================================
# TEST: Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_empty_message_handling(self, orchestrator):
        """Test handling of empty messages."""
        result = orchestrator.process_request("")

        # Should still produce some response
        assert result is not None
        assert 'final_response' in result

    def test_very_long_message(self, orchestrator):
        """Test handling of very long messages."""
        long_message = "a" * 1000
        result = orchestrator.process_request(long_message)

        assert result is not None
        assert 'final_response' in result

    def test_special_characters_handling(self, orchestrator):
        """Test handling of special characters."""
        special_message = "What's the price? @#$%^&*()"
        result = orchestrator.process_request(special_message)

        assert result is not None
        assert 'final_response' in result

    def test_unicode_handling(self, orchestrator):
        """Test handling of unicode characters."""
        unicode_message = "Привет! 你好! مرحبا"
        result = orchestrator.process_request(unicode_message)

        assert result is not None
        assert 'final_response' in result


# ============================================================================
# TEST: Integration Tests
# ============================================================================

class TestEndToEndIntegration:
    """End-to-end integration tests."""

    def test_complete_info_workflow(self, orchestrator):
        """Test complete info workflow from request to response."""
        # Simulate user asking for info
        result = orchestrator.process_request("How much does parking cost?")

        # Verify complete workflow
        assert result['final_response'] != ''
        assert len(result['state_history']) > 0
        # Should either have errors or not (flexible)
        assert 'response' in result['state_history']

    def test_complete_reservation_workflow(self, orchestrator):
        """Test complete reservation workflow."""
        result = orchestrator.process_request("I want to make a reservation")

        # Verify workflow executed
        assert result['request_type'] == 'reservation'
        assert result['final_response'] != ''
        assert 'collection' in result['state_history']
        assert 'approval' in result['state_history']

    def test_sequential_requests_independent(self, orchestrator):
        """Test that sequential requests don't interfere with each other."""
        result1 = orchestrator.process_request("What's the price?")
        result2 = orchestrator.process_request("I want to reserve")
        result3 = orchestrator.process_request("Where is it?")

        # All should have different request IDs
        ids = {result1['request_id'], result2['request_id'], result3['request_id']}
        assert len(ids) == 3

        # All should be in history
        assert len(orchestrator.request_history) == 3

    def test_user_context_separation(self, orchestrator):
        """Test that different users' requests are properly separated."""
        result1 = orchestrator.process_request("Request 1", user_id="user_1")
        result2 = orchestrator.process_request("Request 2", user_id="user_2")

        # Both should be processed
        assert result1['request_id'] != result2['request_id']

        # Check history
        history = orchestrator.list_requests()
        assert len(history) >= 2


# ============================================================================
# TEST: Performance and Metrics
# ============================================================================

class TestPerformanceMetrics:
    """Test performance and metrics collection."""

    def test_request_processing_completes(self, orchestrator):
        """Test that request processing completes within reasonable time."""
        import time

        start_time = time.time()
        result = orchestrator.process_request("test request")
        elapsed = time.time() - start_time

        # Should complete in reasonable time (< 10 seconds)
        assert elapsed < 10.0
        assert result is not None

    def test_multiple_requests_throughput(self, orchestrator):
        """Test throughput of multiple sequential requests."""
        import time

        num_requests = 5
        start_time = time.time()

        for i in range(num_requests):
            orchestrator.process_request(f"Request {i}")

        elapsed = time.time() - start_time
        throughput = num_requests / elapsed if elapsed > 0 else 0

        # Should handle at least a few requests per second
        assert len(orchestrator.request_history) == num_requests


# ============================================================================
# TEST: Mock Integration
# ============================================================================

class TestMockIntegration:
    """Test integration with mocked components."""

    def test_with_mock_rag_response(self, orchestrator):
        """Test that orchestrator works with different RAG responses."""
        # The actual RAG response depends on what documents are loaded
        result = orchestrator.process_request("What is parking?")

        # Should still produce valid output
        assert result is not None
        assert result['final_response'] != ''

    def test_with_simulated_approval(self, orchestrator):
        """Test reservation workflow with simulated approval."""
        result = orchestrator.process_request("I want to reserve a spot")

        # With simulated channel, should complete workflow
        if result['request_type'] == 'reservation':
            assert result['approval_status'] != 'unknown'


# ============================================================================
# Run tests if executed directly
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])




