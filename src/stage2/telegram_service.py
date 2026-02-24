"""
Telegram Integration for Stage 2 LangChain Admin Agent

Background service that listens for Telegram messages from the admin
and processes approval/rejection commands via the LangChain agent tools.
"""

import os
import re
import asyncio
from typing import Optional

try:
    from telegram import Update, Bot
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False


class TelegramAdminService:
    """Telegram bot service for admin approval using LangChain agent."""

    def __init__(self, bot_token: str, admin_agent):
        """
        Initialize Telegram service.

        Args:
            bot_token: Telegram bot token from @BotFather
            admin_agent: LangChain AdminAgent instance to update with responses
        """
        self.bot_token = bot_token
        self.admin_agent = admin_agent
        self.application: Optional[Application] = None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        await update.message.reply_text(
            "👋 Hello! I'm the Parking Admin Bot.\n\n"
            "Send approval/rejection commands:\n"
            "• `approve REQ-xxx` - Approve a request\n"
            "• `reject REQ-xxx reason` - Reject a request\n\n"
            "Use /pending to see pending requests."
        )

    async def pending(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pending command - show pending requests."""
        pending = self.admin_agent.get_pending_requests()

        if not pending:
            await update.message.reply_text("✅ No pending requests!")
            return

        text = "📋 Pending Requests:\n\n"
        for req in pending:
            text += (
                f"ID: `{req['request_id']}`\n"
                f"Name: {req['name']} {req['surname']}\n"
                f"Car: {req['car_number']}\n"
                f"Period: {req['period']}\n"
                f"---\n"
            )

        await update.message.reply_text(text, parse_mode="Markdown")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages with approval/rejection commands."""
        text = update.message.text.strip()
        print(f"\n[TELEGRAM] Received: '{text}'")

        # Parse "approve REQ-xxx"
        approve_match = re.match(r'^approve\s+(REQ-[\w-]+)$', text, re.IGNORECASE)
        if approve_match:
            request_id = approve_match.group(1)
            print(f"[TELEGRAM] ✅ Matched approve: {request_id}")
            self.admin_agent.approval_channel.add_response(
                request_id=request_id,
                approved=True,
                reason="Approved by admin via Telegram"
            )
            print(f"[TELEGRAM] Added to queue, processing...")
            self.admin_agent.process_responses()
            print(f"[TELEGRAM] Processed, replying...")
            await update.message.reply_text(f"✅ Request {request_id} approved!")
            return

        # Parse "reject REQ-xxx reason..."
        reject_match = re.match(r'^reject\s+(REQ-[\w-]+)\s+(.+)$', text, re.IGNORECASE)
        if reject_match:
            request_id = reject_match.group(1)
            reason = reject_match.group(2)
            print(f"[TELEGRAM] ✅ Matched reject: {request_id} - {reason}")
            self.admin_agent.approval_channel.add_response(
                request_id=request_id,
                approved=False,
                reason=reason
            )
            self.admin_agent.process_responses()
            await update.message.reply_text(f"❌ Request {request_id} rejected.\nReason: {reason}")
            return

        # Unknown command
        await update.message.reply_text(
            "❓ Unknown command.\n\n"
            "Use:\n"
            "• `approve REQ-xxx`\n"
            "• `reject REQ-xxx reason`\n"
            "• `/pending` - List pending requests"
        )

    async def run(self):
        """Start the Telegram bot service."""
        if not TELEGRAM_AVAILABLE:
            print("❌ python-telegram-bot not installed")
            print("   Install with: pip install python-telegram-bot")
            return

        print("\n" + "="*70)
        print("🤖 TELEGRAM ADMIN BOT (LangChain)")
        print("="*70)
        print(f"\nStarting bot with token: {self.bot_token[:20]}...")

        self.application = Application.builder().token(self.bot_token).build()

        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("pending", self.pending))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        print("✅ Bot started. Listening for commands...")
        print("   Type /start in Telegram to see available commands\n")

        # Start the bot
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

        try:
            # Keep running
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down...")
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()


def run_telegram_bot():
    """Entry point for Telegram bot service."""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    from src.stage2.admin_agent import create_admin_agent

    # Check for required environment variables
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")

    if not bot_token or not chat_id:
        print("❌ Missing environment variables!")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_ADMIN_CHAT_ID")
        sys.exit(1)

    # Create agent with Telegram channel
    try:
        agent = create_admin_agent(use_telegram=True)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)

    # Run Telegram service
    service = TelegramAdminService(bot_token, agent)

    try:
        asyncio.run(service.run())
    except KeyboardInterrupt:
        print("\n\nBot stopped.")
        sys.exit(0)


if __name__ == "__main__":
    run_telegram_bot()

