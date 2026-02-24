"""
Stage 2 LangChain Integrated Chatbot

Combines RAG chatbot from Stage 1 with LangChain AdminAgent from Stage 2,
creating a complete workflow for parking reservations.
"""

import os
import sys
import time
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.stage1.rag_chatbot import DocumentStore, SimpleRAGChatbot, collect_reservation_interactive
from src.stage2.admin_agent import AdminAgent, create_admin_agent


class Stage2Chatbot:
    """
    Integrated chatbot combining RAG (Stage 1) with LangChain Human-in-the-Loop (Stage 2).

    Features:
    - Answers parking-related questions using RAG
    - Collects reservation details from user
    - Submits to LangChain AdminAgent for approval
    - Tracks request status
    """

    def __init__(
        self,
        rag_store: DocumentStore,
        admin_agent: AdminAgent,
        use_llm: bool = False,
        include_dynamic: bool = True
    ):
        """
        Initialize Stage 2 LangChain chatbot.

        Args:
            rag_store: DocumentStore with parking information
            admin_agent: LangChain AdminAgent for handling approvals
            use_llm: Whether to use OpenAI LLM for responses
            include_dynamic: Whether to include real-time parking data
        """
        self.rag_bot = SimpleRAGChatbot(rag_store, use_llm=use_llm, include_dynamic=include_dynamic)
        self.admin_agent = admin_agent
        self.active_requests = {}  # user_id -> request_id mapping

    def answer_question(self, question: str) -> str:
        """Answer a parking-related question using RAG chatbot."""
        return self.rag_bot.answer(question)

    def initiate_reservation(self, user_info: dict) -> dict:
        """
        Initiate a reservation request via LangChain AdminAgent.

        Args:
            user_info: {name, surname, car_number, period}

        Returns:
            {
                "success": bool,
                "request_id": str (if successful),
                "message": str,
                "status": str
            }
        """
        try:
            # Submit to admin agent using tool
            request_id = self.admin_agent.submit_request(
                name=user_info.get("name"),
                surname=user_info.get("surname"),
                car_number=user_info.get("car_number"),
                period=user_info.get("period")
            )

            return {
                "success": True,
                "request_id": request_id,
                "message": (
                    f"✅ Reservation request submitted!\n"
                    f"Request ID: {request_id}\n"
                    f"Your request has been sent to the administrator for review.\n"
                    f"We will notify you when it's approved or rejected."
                ),
                "status": "pending"
            }
        except Exception as e:
            return {
                "success": False,
                "request_id": None,
                "message": f"❌ Error submitting request: {str(e)}",
                "status": "error"
            }

    def check_request_status(self, request_id: str) -> dict:
        """
        Check status of a reservation request via LangChain AdminAgent.

        Args:
            request_id: The request ID to check

        Returns:
            Status dictionary from agent
        """
        return self.admin_agent.check_status(request_id)

    def wait_for_approval(
        self,
        request_id: str,
        timeout_sec: float = 60,
        poll_interval_sec: float = 1
    ) -> dict:
        """
        Wait for admin approval with timeout.

        Args:
            request_id: Request ID to wait for
            timeout_sec: Maximum time to wait
            poll_interval_sec: How often to poll for updates

        Returns:
            Final status of request
        """
        elapsed = 0
        while elapsed < timeout_sec:
            self.admin_agent.process_responses()
            status = self.check_request_status(request_id)

            if status["status"] != "pending":
                return status

            time.sleep(poll_interval_sec)
            elapsed += poll_interval_sec

        return {
            "request_id": request_id,
            "status": "timeout",
            "approved": False,
            "reason": f"No response from admin within {timeout_sec}s"
        }

    def interactive_chat(self, use_llm: bool = False):
        """
        Run interactive chat mode - ask questions or make reservations.

        Commands:
        - 'reserve' - Make a reservation
        - 'status <request_id>' - Check reservation status
        - 'exit' - Exit chat
        - Any other text - Ask about parking info
        """
        print("\n" + "="*70)
        print("🅿️  PARKING RESERVATION CHATBOT (LangChain Stage 2)")
        print("="*70)
        print("\nCommands:")
        print("  'reserve' - Make a new reservation")
        print("  'status <request_id>' - Check reservation status")
        print("  'exit' - Exit chat")
        print("  Or ask anything about parking!\n")

        while True:
            try:
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                if user_input.lower() == "exit":
                    print("Goodbye! 👋\n")
                    break

                if user_input.lower() == "reserve":
                    # Collect reservation details
                    reservation_details = collect_reservation_interactive()
                    if reservation_details:
                        result = self.initiate_reservation(reservation_details)
                        print(f"\n{result['message']}")

                        if result["success"]:
                            req_id = result["request_id"]
                            print(f"\n⏳ Waiting for admin response (timeout: 60s)...")
                            status = self.wait_for_approval(req_id, timeout_sec=60)

                            if status["approved"]:
                                print(f"✅ YOUR REQUEST HAS BEEN APPROVED!")
                                print(f"   Request ID: {status['request_id']}")
                            else:
                                print(f"❌ YOUR REQUEST HAS BEEN REJECTED")
                                print(f"   Request ID: {status['request_id']}")
                                if status.get("reason"):
                                    print(f"   Reason: {status['reason']}")
                        print()

                elif user_input.lower().startswith("status "):
                    req_id = user_input[7:].strip()
                    status = self.check_request_status(req_id)
                    print(f"\nRequest Status: {status['request_id']}")
                    print(f"Status: {status['status'].upper()}")
                    print(f"Approved: {'✅ Yes' if status['approved'] else '❌ No'}")
                    if status.get("reason"):
                        print(f"Details: {status['reason']}")
                    print()

                else:
                    # Answer question about parking
                    answer = self.answer_question(user_input)
                    print(f"\n{answer}\n")

            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋\n")
                break
            except Exception as e:
                print(f"Error: {e}\n")

    def reserve_command(self):
        """Single reservation submission mode."""
        print("\n" + "="*70)
        print("🚗 MAKE A RESERVATION")
        print("="*70)

        reservation_details = collect_reservation_interactive()
        if not reservation_details:
            return

        result = self.initiate_reservation(reservation_details)
        print(f"\n{result['message']}")

        if result["success"]:
            req_id = result["request_id"]
            print(f"\n⏳ Waiting for admin response (timeout: 60s)...")
            status = self.wait_for_approval(req_id, timeout_sec=60)

            if status["approved"]:
                print(f"\n✅ YOUR REQUEST HAS BEEN APPROVED!")
                print(f"   Request ID: {status['request_id']}")
            else:
                print(f"\n❌ YOUR REQUEST HAS BEEN REJECTED")
                print(f"   Request ID: {status['request_id']}")
                if status.get("reason"):
                    print(f"   Reason: {status['reason']}")

        print()

    def status_command(self, request_id: str):
        """Check status of a specific request."""
        print("\n" + "="*70)
        print(f"📋 REQUEST STATUS: {request_id}")
        print("="*70)

        status = self.check_request_status(request_id)

        print(f"\nStatus: {status['status'].upper()}")
        print(f"Approved: {'✅ Yes' if status['approved'] else '❌ No'}")

        if status.get("reason"):
            print(f"Details: {status['reason']}")

        if status.get("response_time"):
            print(f"Response Time: {status['response_time']}")

        print()

