"""
Stage 4: LangGraph Orchestrator

Wrapper around the LangGraph for easy integration and management.
Provides a simple interface for processing requests through the complete workflow.
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Lazy import to avoid hanging on module load
# These will be imported when create_orchestrator() is called
# from src.stage4.graph import create_orchestration_graph, WorkflowState, UserInput

# Import these at module level as they're lightweight
def _get_graph_module():
    """Lazy import graph module to avoid hanging on module load."""
    from src.stage4.graph import create_orchestration_graph, WorkflowState, UserInput
    return create_orchestration_graph, WorkflowState, UserInput


class LangGraphOrchestrator:
    """
    Main orchestrator for the complete parking reservation system.

    Manages the LangGraph workflow, request processing, and integration with all stages.

    Features:
    - Process user requests through the complete workflow
    - Track request status and history
    - Handle different request types (info, reservation, status)
    - Persistent request tracking
    """

    def __init__(
        self,
        use_llm: bool = False,
        use_telegram: bool = False,
        llm: Optional[Any] = None,
        verbose: bool = False,
    ):
        """
        Initialize the orchestrator.

        Args:
            use_llm: Whether to use OpenAI LLM for better responses
            use_telegram: Whether to use Telegram for admin notifications
            llm: Optional LangChain LLM instance
            verbose: Whether to print detailed workflow information
        """
        self.use_llm = use_llm
        self.use_telegram = use_telegram
        self.llm = llm
        self.verbose = verbose
        self.admin_agent = None  # Store reference to admin agent for cleanup

        # Lazy import to avoid hanging
        create_orchestration_graph, _, _ = _get_graph_module()

        # Create and compile the graph
        graph_with_resources = create_orchestration_graph(
            use_llm=use_llm,
            use_telegram=use_telegram,
            llm=llm,
        )

        # Store the graph and admin agent reference
        self.graph = graph_with_resources
        self.admin_agent = graph_with_resources._admin_agent

        # Track processed requests
        self.request_history: Dict[str, Dict[str, Any]] = {}


    def process_request(self, user_message: str, user_id: str = "user_001") -> Dict[str, Any]:
        """
        Process a user request through the complete workflow.

        Args:
            user_message: The user's input message
            user_id: Unique identifier for the user (default: generic user)

        Returns:
            Dictionary with:
            - final_response: String response to the user
            - request_id: Unique workflow request ID
            - request_type: Type of request (info/reservation/status_check/unknown)
            - approval_status: For reservations, the approval outcome
            - storage_success: Whether the data was saved
            - state_history: List of nodes visited in the workflow
            - errors: Any errors encountered
        """

        if self.verbose:
            print(f"\n📥 Processing request from {user_id}: {user_message}")

        # Build initial state
        initial_state: Dict[str, Any] = {
            "user_input": {
                "user_id": user_id,
                "message": user_message,
                "timestamp": datetime.now().isoformat(),
            },
            "request_type": "unknown",
            "final_response": "",
            "request_id": "",
            "errors": [],
            "state_history": [],
            "storage_success": False,
            "storage_message": "",
        }

        # Execute the graph
        result_state = self.graph.invoke(initial_state)

        # Extract relevant results
        output = {
            "final_response": result_state.get("final_response", ""),
            "request_id": result_state.get("request_id", ""),
            "request_type": result_state.get("request_type", "unknown"),
            "approval_status": result_state.get("approval_result", {}).get("status", "N/A"),
            "storage_success": result_state.get("storage_success", False),
            "storage_message": result_state.get("storage_message", ""),
            "state_history": result_state.get("state_history", []),
            "errors": result_state.get("errors", []),
        }

        # Store in history
        self.request_history[result_state["request_id"]] = {
            "user_id": user_id,
            "user_message": user_message,
            "timestamp": datetime.now().isoformat(),
            "output": output,
            "full_state": result_state,
        }

        if self.verbose:
            print(f"✅ Request processed")
            print(f"   Type: {output['request_type']}")
            print(f"   Path: {' → '.join(output['state_history'])}")
            if output['errors']:
                print(f"   Errors: {output['errors']}")

        return output


    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a previously processed request.

        Args:
            request_id: The request ID to look up

        Returns:
            Dictionary with request information, or None if not found
        """
        if request_id in self.request_history:
            return self.request_history[request_id]
        return None


    def list_requests(self) -> List[Dict[str, Any]]:
        """
        Get a list of all processed requests (summary).

        Returns:
            List of request summaries with ID, timestamp, and outcome
        """
        summaries = []
        for request_id, record in self.request_history.items():
            summaries.append({
                "request_id": request_id,
                "user_id": record["user_id"],
                "user_message": record["user_message"],
                "timestamp": record["timestamp"],
                "request_type": record["output"]["request_type"],
                "approval_status": record["output"]["approval_status"],
                "storage_success": record["output"]["storage_success"],
            })
        return summaries


    def print_summary(self):
        """Print a summary of all processed requests."""
        print("\n" + "="*80)
        print("📊 ORCHESTRATION SUMMARY")
        print("="*80)

        requests = self.list_requests()
        print(f"\nTotal Requests Processed: {len(requests)}\n")

        for i, req in enumerate(requests, 1):
            print(f"{i}. {req['request_id']}")
            print(f"   User: {req['user_id']}")
            print(f"   Message: {req['user_message']}")
            print(f"   Type: {req['request_type']}")
            if req['request_type'] == 'reservation':
                print(f"   Approval: {req['approval_status']}")
                print(f"   Saved: {'✅' if req['storage_success'] else '❌'}")
            print()

    def close(self):
        """Close resources and cleanup (especially Telegram bot)."""
        if self.admin_agent:
            try:
                self.admin_agent.close()
            except Exception as e:
                print(f"⚠️  Error closing admin agent: {e}")

    def cleanup_resources(self):
        """Alias for close() - cleanup all resources."""
        self.close()

    def interactive_mode(self):
        """
        Run the orchestrator in interactive mode.
        Allows the user to chat with the system continuously.
        """
        print("\n" + "="*80)
        print("🤖 PARKING RESERVATION CHATBOT - Stage 4 Orchestration")
        print("="*80)
        print("\nWelcome! I can help you with:")
        print("  - Answer questions about parking (try: 'info')")
        print("  - Create parking reservations (try: 'reserve')")
        print("  - Check reservation status (try: 'status')")

        print("\n" + "="*80)
        print("📋 RESERVATION FORMAT")
        print("="*80)
        print("\nFormat: reserve <FirstName> <LastName> <CarNumber> <Dates>")
        print("\nExamples:")
        print("  Russian:  reserve Иван Петров RS1234 с 5 по 12 июля 2026")
        print("  English:  reserve John Smith ABC123 from 5 march to 12 march 2026")
        print("\nSupported date formats:")
        print("  Russian:  'с 5 по 12 июля 2026' (same month)")
        print("  English:  'from 5 march to 12 march 2026'")
        print("\nType 'help' for more options, 'summary' to see all requests, 'exit' to quit.\n")

        user_id = f"user_{datetime.now().strftime('%H%M%S')}"

        while True:
            try:
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                if user_input.lower() == "exit":
                    print("\nThank you for using our service! Goodbye! 👋")
                    self.print_summary()
                    self.close()
                    break

                if user_input.lower() == "summary":
                    self.print_summary()
                    continue

                if user_input.lower() == "help":
                    print("\n" + "-"*80)
                    print("HELP - Available Commands")
                    print("-"*80)
                    print("General:")
                    print("  'help'     - Show this help message")
                    print("  'summary'  - Show all processed requests")
                    print("  'exit'     - Exit the chatbot\n")
                    print("Request Types:")
                    print("  'info'     - Ask about parking information")
                    print("    Example: What is the parking cost?")
                    print("  'reserve'  - Make a new reservation")
                    print("    Format: reserve <FirstName> <LastName> <CarNumber> <DateRange>")
                    print("  'status'   - Check reservation status")
                    print("    Example: check status REQ-20260225231021-001\n")
                    print("Reservation Format Examples:")
                    print("  Russian:  reserve Иван Петров RS1234 с 5 по 12 июля 2026")
                    print("  English:  reserve John Smith ABC123 from 5 march to 12 march 2026")
                    print("-"*80 + "\n")
                    continue

                # Process the request
                result = self.process_request(user_input, user_id)

                print(f"\nBot: {result['final_response']}\n")

                # Show metadata if requested
                if "debug" in user_input.lower():
                    print("\n" + "-"*40)
                    print("DEBUG INFO:")
                    print(f"Request ID: {result['request_id']}")
                    print(f"Type: {result['request_type']}")
                    print(f"Path: {' → '.join(result['state_history'])}")
                    if result['errors']:
                        print(f"Errors: {result['errors']}")
                    print("-"*40 + "\n")

            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye! 👋")
                self.print_summary()
                self.close()
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")
                continue


def create_orchestrator(
    use_llm: bool = False,
    use_telegram: bool = False,
    verbose: bool = True,
) -> LangGraphOrchestrator:
    """
    Factory function to create an orchestrator instance.

    Args:
        use_llm: Whether to use OpenAI LLM
        use_telegram: Whether to use Telegram
        verbose: Whether to print debug information

    Returns:
        Configured LangGraphOrchestrator instance
    """
    return LangGraphOrchestrator(
        use_llm=use_llm,
        use_telegram=use_telegram,
        verbose=verbose,
    )

