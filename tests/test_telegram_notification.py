#!/usr/bin/env python
"""
Test script to verify Telegram notification functionality
"""

import os
import sys
import pytest
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent))

from src.stage2.admin_agent import ReservationRequest, TelegramApprovalChannel

def test_telegram_notification():
    """Test sending a notification to Telegram"""

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    admin_chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")

    if not bot_token or not admin_chat_id:
        print("❌ Telegram credentials not configured in .env")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_ADMIN_CHAT_ID")
        # Skip the test if credentials are not available
        pytest.skip("Telegram credentials not configured")

    print("✅ Telegram credentials found")
    print(f"   Bot Token: {bot_token[:20]}...")
    print(f"   Chat ID: {admin_chat_id}\n")

    # Create a test request
    test_request = ReservationRequest(
        request_id="REQ-TEST-001",
        name="Test",
        surname="User",
        car_number="TST123",
        period="2026-02-24 14:00 - 2026-02-24 16:00",
        created_at="2026-02-24T14:00:00"
    )

    print("🚀 Attempting to send test notification...\n")

    # Create channel and send
    try:
        channel = TelegramApprovalChannel(bot_token, admin_chat_id)
        success = channel.send_request(test_request)

        assert success, "Failed to send notification"

        print("✅ SUCCESS! Telegram notification sent!")
        print("\nCheck your Telegram chat for message:")
        print("   🚗 New Reservation Request")
        print("   Request ID: REQ-TEST-001")
        print("   Name: Test User")
        print("   Car Number: TST123")
        print("   Period: 2026-02-24 14:00 - 2026-02-24 16:00")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
