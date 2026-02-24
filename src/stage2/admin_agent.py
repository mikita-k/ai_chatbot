"""
Stage 2 LangChain: Human-in-the-Loop Admin Agent

Implementation using LangChain framework:
- Tools for admin operations (submit, check status, process responses)
- Agent executor for orchestrating tool calls
- Integrated database persistence
- Support for Telegram and simulated approval channels
"""

import os
import threading
from typing import Optional, Dict, List, Any
from datetime import datetime

from langchain.tools import tool
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate

try:
    # Try new API (langchain >= 0.2.0)
    from langchain.agents import create_tool_calling_agent, AgentExecutor
except ImportError:
    # Fallback for older versions
    AgentExecutor = None
    create_tool_calling_agent = None

from .database import AdminApprovalDatabase, ReservationRequest
from .approval_channels import ApprovalChannel, SimulatedApprovalChannel, TelegramApprovalChannel


class AdminAgent:
    """
    LangChain-based admin agent for handling reservation approvals.

    Uses tool-calling pattern with LangChain to:
    1. Submit reservation requests
    2. Check request status
    3. Process admin responses
    4. Manage request lifecycle
    """

    def __init__(
        self,
        approval_channel: Optional[ApprovalChannel] = None,
        db_path: str = "data/dynamic/approvals.db",
        llm: Optional[BaseLanguageModel] = None,
    ):
        """
        Initialize LangChain admin agent.

        Args:
            approval_channel: Channel for communication with admin (defaults to simulated)
            db_path: Path to SQLite database for storing requests
            llm: LangChain LLM instance (optional, used for agent reasoning)
        """
        self.approval_channel = approval_channel or SimulatedApprovalChannel(auto_approve=True)
        self.db = AdminApprovalDatabase(db_path)
        self.request_counter = 0
        self._request_lock = threading.Lock()
        self.llm = llm

        # Register tools for the agent
        self.tools = self._create_tools()

        # Create agent if LLM is provided
        if self.llm:
            self.agent_executor = self._create_agent_executor()
        else:
            self.agent_executor = None

    def _create_tools(self) -> List:
        """Create LangChain tools for admin operations."""
        agent = self

        @tool
        def submit_reservation(
            name: str,
            surname: str,
            car_number: str,
            period: str,
        ) -> str:
            """
            Submit a new parking reservation request to the administrator for approval.

            Args:
                name: Customer first name
                surname: Customer last name
                car_number: Vehicle registration number (e.g., ABC123)
                period: Reservation period (e.g., '2026-02-20 10:00 - 2026-02-20 12:00')

            Returns:
                Request ID for tracking the submission
            """
            return agent._submit_request_impl(name, surname, car_number, period)

        @tool
        def check_request_status(request_id: str) -> Dict[str, Any]:
            """
            Check the current status of a reservation request.

            Args:
                request_id: The request ID to check (e.g., 'REQ-20260220100000-001')

            Returns:
                Dictionary with request status information
            """
            return agent._check_status_impl(request_id)

        @tool
        def process_admin_responses() -> str:
            """
            Poll for and process new admin responses.
            Updates the status of requests that have been approved or rejected.

            Returns:
                Summary of processed responses
            """
            return agent._process_responses_impl()

        @tool
        def get_pending_requests() -> List[Dict]:
            """
            Get all currently pending reservation requests waiting for admin approval.

            Returns:
                List of pending request details
            """
            requests = agent.db.get_all_requests(status="pending")
            return [r.to_dict() for r in requests]

        @tool
        def get_all_requests() -> List[Dict]:
            """
            Get all reservation requests (for reporting and auditing).

            Returns:
                List of all requests with their current status
            """
            requests = agent.db.get_all_requests()
            return [r.to_dict() for r in requests]

        return [
            submit_reservation,
            check_request_status,
            process_admin_responses,
            get_pending_requests,
            get_all_requests,
        ]

    def _create_agent_executor(self):
        """Create LangChain agent executor with tools."""
        if not AgentExecutor or not create_tool_calling_agent:
            raise RuntimeError(
                "LangChain agent tools not available. "
                "Update langchain: pip install --upgrade langchain"
            )

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful parking reservation admin agent. Use the provided tools to help manage and process reservation requests."),
            ("user", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
        return executor

    def invoke_agent(self, user_input: str) -> str:
        """
        Invoke the LangChain agent with natural language input.

        Only works if LLM is provided during initialization.

        Args:
            user_input: Natural language instruction for the agent

        Returns:
            Agent response
        """
        if not self.agent_executor:
            raise RuntimeError("Agent executor not initialized. Provide an LLM to use invoke_agent().")

        result = self.agent_executor.invoke({"input": user_input})
        return result.get("output", "")

    def submit_request(self, name: str, surname: str, car_number: str, period: str) -> str:
        """
        Submit a new reservation request for admin approval.

        Args:
            name: Customer first name
            surname: Customer last name
            car_number: Vehicle registration number
            period: Reservation time period

        Returns:
            request_id: Unique identifier for tracking this request
        """
        return self._submit_request_impl(name, surname, car_number, period)

    def _submit_request_impl(self, name: str, surname: str, car_number: str, period: str) -> str:
        """Internal implementation of request submission."""
        with self._request_lock:
            self.request_counter += 1
            request_id = f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.request_counter:03d}"

        request = ReservationRequest(
            request_id=request_id,
            name=name,
            surname=surname,
            car_number=car_number,
            period=period,
            created_at=datetime.now().isoformat(),
            status="pending"
        )

        # Save to database
        self.db.save_request(request)

        # Send to admin
        sent = self.approval_channel.send_request(request)
        if not sent:
            print(f"⚠️  Could not send request {request_id} to admin directly")
            print(f"    Request will stay PENDING - admin can respond via polling\n")

        return request_id

    def check_status(self, request_id: str) -> Dict:
        """
        Check the status of a reservation request.

        Args:
            request_id: The request ID to check

        Returns:
            Status information dictionary
        """
        return self._check_status_impl(request_id)

    def _check_status_impl(self, request_id: str) -> Dict:
        """Internal implementation of status check."""
        request = self.db.get_request(request_id)
        if not request:
            return {
                "request_id": request_id,
                "status": "not_found",
                "approved": False,
                "reason": "Request not found"
            }

        return {
            "request_id": request_id,
            "status": request.status,
            "approved": request.status == "approved",
            "reason": request.admin_response,
            "response_time": request.response_time
        }

    def process_responses(self) -> None:
        """
        Poll for admin responses and update request statuses.
        Should be called periodically (or in a background thread).
        """
        self._process_responses_impl()

    def _process_responses_impl(self) -> str:
        """Internal implementation of response processing."""
        responses = self.approval_channel.get_responses()

        if not responses:
            return "No new responses to process."

        processed = 0
        for response in responses:
            request_id = response.get("request_id")
            approved = response.get("approved", False)
            reason = response.get("reason", "")

            request = self.db.get_request(request_id)
            if request:
                request.status = "approved" if approved else "rejected"
                request.admin_response = reason
                request.response_time = datetime.now().isoformat()
                self.db.save_request(request)
                processed += 1

        return f"Processed {processed} response(s)."

    def get_pending_requests(self) -> List[Dict]:
        """Get all pending requests for admin dashboard."""
        requests = self.db.get_all_requests(status="pending")
        return [r.to_dict() for r in requests]

    def get_all_requests(self) -> List[Dict]:
        """Get all requests (for reporting/auditing)."""
        requests = self.db.get_all_requests()
        return [r.to_dict() for r in requests]

    def close(self):
        """Clean up resources."""
        self.approval_channel.close()


def create_admin_agent(
    use_telegram: bool = False,
    llm: Optional[BaseLanguageModel] = None,
) -> AdminAgent:
    """
    Factory function to create a LangChain admin agent with the specified channel.

    Args:
        use_telegram: If True, use Telegram channel (requires env vars)
                     If False, use simulated channel (for testing)
        llm: Optional LangChain LLM instance for agent reasoning

    Returns:
        Configured AdminAgent instance
    """
    if use_telegram:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")

        if not bot_token or not chat_id:
            raise ValueError(
                "Telegram channel requires TELEGRAM_BOT_TOKEN and TELEGRAM_ADMIN_CHAT_ID "
                "environment variables"
            )

        channel = TelegramApprovalChannel(bot_token, chat_id)
    else:
        # Default: simulated channel (no external dependencies)
        channel = SimulatedApprovalChannel(auto_approve=True, approval_delay_sec=1.0)

    return AdminAgent(approval_channel=channel, llm=llm)


if __name__ == "__main__":
    # Quick test
    print("Testing LangChain AdminAgent with simulated approval channel...\n")

    agent = create_admin_agent(use_telegram=False)

    # Submit a test request using tool
    print("Submitting test request...")
    req_id = agent.submit_request(
        name="John",
        surname="Doe",
        car_number="ABC123",
        period="2026-02-20 10:00 - 2026-02-20 12:00"
    )
    print(f"Request ID: {req_id}")
    print(f"Status: {agent.check_status(req_id)}\n")

    # Wait for admin "response"
    print("Waiting for admin response (1 second)...")
    import time
    time.sleep(1.5)

    # Process responses
    print("Processing responses...")
    agent.process_responses()

    # Check status again
    print(f"Updated status: {agent.check_status(req_id)}\n")

    # Show all requests
    print("All requests:")
    for req in agent.get_all_requests():
        print(f"  {req['request_id']}: {req['name']} {req['surname']} - {req['status']}")






