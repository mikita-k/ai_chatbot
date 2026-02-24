"""
Approval channels for Stage 2 LangChain - Admin communication via Telegram or simulation
"""

import queue
import time
import threading
from abc import ABC, abstractmethod
from typing import Dict, List
from .database import ReservationRequest


class ApprovalChannel(ABC):
    """Abstract base class for approval channels (Telegram, Email, etc.)"""

    @abstractmethod
    def send_request(self, request: ReservationRequest) -> bool:
        """Send reservation request to admin. Returns True if sent successfully."""
        pass

    @abstractmethod
    def get_responses(self) -> List[Dict]:
        """Poll for admin responses. Returns list of {request_id, approved, reason}."""
        pass

    @abstractmethod
    def close(self):
        """Clean up resources."""
        pass


class TelegramApprovalChannel(ApprovalChannel):
    """
    Telegram-based approval channel.

    The admin receives messages in a Telegram chat and responds with:
    - "approve <request_id>" to approve
    - "reject <request_id> <reason>" to reject
    """

    def __init__(self, bot_token: str, chat_id: str | int):
        """
        Initialize Telegram channel.

        Args:
            bot_token: Telegram bot token (from @BotFather)
            chat_id: Chat ID where admin will receive requests
        """
        self.bot_token = bot_token
        self.chat_id = str(chat_id)
        self.pending_requests: Dict[str, ReservationRequest] = {}
        self.responses: queue.Queue = queue.Queue()

        # Try to import telegram library
        try:
            from telegram import Update, Bot
            from telegram.ext import Application, CommandHandler, MessageHandler, filters
            self.telegram_available = True
            self.Bot = Bot
            self.Update = Update
            self.Application = Application
            self.CommandHandler = CommandHandler
            self.MessageHandler = MessageHandler
            self.filters = filters
        except ImportError:
            self.telegram_available = False
            print(
                "Warning: python-telegram-bot not installed. "
                "Install it with: pip install python-telegram-bot"
            )

    def send_request(self, request: ReservationRequest) -> bool:
        """Send reservation request to Telegram chat."""
        if not self.telegram_available:
            print(f"[DEBUG] Would send request to Telegram (not available): {request.request_id}")
            return False

        try:
            import requests

            message = (
                f"🚗 *New Reservation Request*\n\n"
                f"Request ID: `{request.request_id}`\n"
                f"Name: {request.name} {request.surname}\n"
                f"Car Number: {request.car_number}\n"
                f"Period: {request.period}\n\n"
                f"Reply with:\n"
                f"`approve {request.request_id}`\n"
                f"`reject {request.request_id} <reason>`"
            )

            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }

            response = requests.post(url, json=payload, timeout=5)

            if response.status_code == 200:
                self.pending_requests[request.request_id] = request
                return True
            else:
                print(f"Telegram API error: {response.text}")
                return False

        except Exception as e:
            print(f"Error sending request to Telegram: {e}")
            return False

    def get_responses(self) -> List[Dict]:
        """Poll for admin responses from Telegram."""
        responses = []
        try:
            while True:
                response = self.responses.get_nowait()
                responses.append(response)
        except queue.Empty:
            pass
        return responses

    def add_response(self, request_id: str, approved: bool, reason: str = ""):
        """Add a response to the queue (called by message handler)."""
        self.responses.put({
            "request_id": request_id,
            "approved": approved,
            "reason": reason
        })

    def close(self):
        """Close Telegram connection."""
        pass


class SimulatedApprovalChannel(ApprovalChannel):
    """
    Simulated approval channel for testing (no external dependencies).

    Default behavior: approves all requests after a short delay.
    Can be configured to reject specific requests.
    """

    def __init__(self, auto_approve: bool = True, approval_delay_sec: float = 1.0):
        """
        Initialize simulated channel.

        Args:
            auto_approve: Whether to auto-approve requests (default True)
            approval_delay_sec: Delay before auto-approval (simulates admin review)
        """
        self.auto_approve = auto_approve
        self.approval_delay_sec = approval_delay_sec
        self.pending_requests: Dict[str, float] = {}  # request_id -> creation_time
        self.responses: Dict[str, Dict] = {}  # request_id -> response

    def send_request(self, request: ReservationRequest) -> bool:
        """Store request and simulate admin review."""
        self.pending_requests[request.request_id] = time.time()

        # Schedule auto-approval after delay
        if self.auto_approve:
            def auto_approve_task():
                time.sleep(self.approval_delay_sec)
                self.responses[request.request_id] = {
                    "request_id": request.request_id,
                    "approved": True,
                    "reason": "Auto-approved by simulator"
                }

            thread = threading.Thread(target=auto_approve_task, daemon=True)
            thread.start()

        return True

    def add_response(self, request_id: str, approved: bool, reason: str = ""):
        """Manually add a response (for testing without waiting for auto-approval)."""
        self.responses[request_id] = {
            "request_id": request_id,
            "approved": approved,
            "reason": reason
        }

    def get_responses(self) -> List[Dict]:
        """Return all responses collected so far."""
        result = list(self.responses.values())
        self.responses.clear()
        return result

    def close(self):
        """Clean up resources."""
        pass

